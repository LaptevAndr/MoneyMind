from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from datetime import timedelta

# Модель для категорий доходов/расходов (Еда, Транспорт, Зарплата)
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')
    name = models.CharField(max_length=100)
    # Тип категории: либо доход ('income'), либо расход ('expense')
    TYPE_CHOICES = (
        ('income', 'Доход'),
        ('expense', 'Расход'),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    # Поле для отметки кредитных категорий
    is_credit_related = models.BooleanField(default=False, verbose_name='Связано с кредитами')

    # Метод для отображения объекта в админке
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'type'], 
                name='unique_category_per_user'
            )
        ]

# Главная модель — транзакция (любой доход или расход)
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Связь с пользователем. Если user удалится, все его транзакции тоже удалятся (CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Сумма. 10 цифр всего
    category = models.ForeignKey(Category, on_delete=models.CASCADE) # Связь с категорией
    date = models.DateField() # Дата операции
    description = models.TextField(blank=True) # Описание, может быть пустым
    
    # Связь с кредитом (если транзакция - платеж по кредиту)
    loan = models.ForeignKey('Loan', on_delete=models.SET_NULL, null=True, blank=True, 
                           verbose_name='Связанный кредит')

    def __str__(self):
        return f"{self.date} - {self.category}: {self.amount}"

# МОДЕЛЬ: Цели накопления
class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='Название цели')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Целевая сумма')
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Текущая сумма')
    deadline = models.DateField(verbose_name='Срок достижения', null=True, blank=True)
    priority = models.IntegerField(verbose_name='Приоритет', default=1)
    is_completed = models.BooleanField(default=False, verbose_name='Выполнена')
    
    # Автоматически рассчитываем процент выполнения
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    def __str__(self):
        return f"{self.name} - {self.progress_percentage:.1f}%"

# МОДЕЛЬ: Кредиты
class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название кредита")
    initial_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма кредита")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Процентная ставка (%)", default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Выплачено")
    start_date = models.DateField(default=timezone.now, verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def current_total_amount(self):
        """Текущая общая сумма с начисленными процентами"""
        if self.interest_rate == Decimal('0'):
            return self.initial_amount
        
        months_passed = self.months_passed
        monthly_rate = self.interest_rate / Decimal('100') / Decimal('12')
        return self.initial_amount * (Decimal('1') + monthly_rate) ** months_passed
    
    @property
    def remaining_amount(self):
        """Оставшаяся сумма с учетом процентов"""
        return self.current_total_amount - self.paid_amount
    
    @property
    def accrued_interest(self):
        """Начисленные проценты"""
        return self.current_total_amount - self.initial_amount
    
    @property
    def months_passed(self):
        """Количество прошедших месяцев"""
        today = timezone.now().date()
        if today < self.start_date:
            return 0
        months = (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month)
        return max(0, months)
    
    @property
    def total_months(self):
        """Общее количество месяцев кредита"""
        total = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        return max(1, total)  # Гарантируем минимум 1 месяц
    
    @property
    def months_remaining(self):
        """Оставшееся количество месяцев"""
        return max(0, self.total_months - self.months_passed)
    
    @property
    def monthly_payment(self):
        """Ежемесячный платеж (аннуитетный)"""
        # Если кредит без процентов
        if self.interest_rate == Decimal('0'):
            if self.total_months == 0:
                return self.initial_amount
            return self.initial_amount / Decimal(str(self.total_months))
        
        # Расчет аннуитетного платежа
        monthly_rate = self.interest_rate / Decimal('100') / Decimal('12')
        total_months_dec = Decimal(str(self.total_months))
        
        # Проверка на нулевой знаменатель
        if monthly_rate == Decimal('0') or total_months_dec == Decimal('0'):
            if total_months_dec == Decimal('0'):
                return self.initial_amount
            return self.initial_amount / total_months_dec
        
        # Расчет по формуле аннуитета
        numerator = self.initial_amount * monthly_rate * (Decimal('1') + monthly_rate) ** total_months_dec
        denominator = (Decimal('1') + monthly_rate) ** total_months_dec - Decimal('1')
        
        # Защита от деления на ноль
        if denominator == Decimal('0'):
            # Возвращаем простое деление на количество месяцев
            return self.initial_amount / total_months_dec
        
        return numerator / denominator
    
    @property
    def progress_percentage(self):
        """Процент выплаты"""
        if self.current_total_amount == Decimal('0'):
            return Decimal('0')
        return (self.paid_amount / self.current_total_amount) * Decimal('100')
    
    def __str__(self):
        return f"{self.name} - {self.remaining_amount:.2f}₽"