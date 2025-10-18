from django.contrib import admin
from .models import Category, Transaction, SavingsGoal, Loan

# Регистрация модели Category с кастомизацией
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_credit_related')  # Поля для отображения в списке
    list_filter = ('type', 'is_credit_related')  # Фильтры в правой панели
    search_fields = ('name',)  # Поля для поиска

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date', 'loan')
    list_filter = ('category', 'date', 'loan')
    search_fields = ('description', 'category__name')

class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'target_amount', 'current_amount', 'progress_percentage', 'is_completed')
    list_filter = ('is_completed',)

class LoanAdmin(admin.ModelAdmin):
    list_display = ['name', 'initial_amount', 'interest_rate', 'paid_amount', 'remaining_amount', 'start_date', 'end_date']
    list_filter = ['start_date', 'end_date', 'interest_rate']
    search_fields = ['name']
    readonly_fields = ['current_total_amount', 'remaining_amount', 'accrued_interest', 'months_passed', 'months_remaining', 'monthly_payment', 'progress_percentage']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'initial_amount', 'interest_rate', 'paid_amount')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date')
        }),
        ('Автоматически рассчитываемые поля', {
            'fields': ('current_total_amount', 'remaining_amount', 'accrued_interest', 'months_passed', 'months_remaining', 'monthly_payment', 'progress_percentage'),
            'classes': ('collapse',)
        }),
    )
    
    def remaining_amount(self, obj):
        return f"{obj.remaining_amount:.2f} ₽"
    remaining_amount.short_description = 'Остаток долга'
    
    def current_total_amount(self, obj):
        return f"{obj.current_total_amount:.2f} ₽"
    current_total_amount.short_description = 'Текущая сумма'
    
    def accrued_interest(self, obj):
        return f"{obj.accrued_interest:.2f} ₽"
    accrued_interest.short_description = 'Начисленные проценты'
    
    def monthly_payment(self, obj):
        return f"{obj.monthly_payment:.2f} ₽"
    monthly_payment.short_description = 'Ежемесячный платеж'
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = 'Прогресс выплаты'

# Регистрация моделей в админке
admin.site.register(Category, CategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(SavingsGoal, SavingsGoalAdmin)
admin.site.register(Loan, LoanAdmin)