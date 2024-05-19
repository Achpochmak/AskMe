from django import template

register = template.Library()

@register.filter
def filter_formset(answer_formsets, question_id):
    return [form for qid, form in answer_formsets if qid == question_id]
