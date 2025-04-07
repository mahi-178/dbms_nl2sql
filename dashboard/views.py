from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
import json
import logging

from .models import Query, QueryFeedback
from .forms import RegistrationForm, QueryForm, QueryFeedbackForm
from .llm_service import LLMService
from .db_service import DatabaseService

def index(request):
    """Landing page view"""
    return render(request, 'dashboard/index.html')

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard:query')
    else:
        form = RegistrationForm()
    
    return render(request, 'dashboard/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard:query')
    else:
        form = AuthenticationForm()
    
    return render(request, 'dashboard/login.html', {'form': form})

@login_required
def query_view(request):
    """Main query interface view"""
    db_service = DatabaseService()
    schema_info, schema_str = db_service.get_schema_info()
    
    form = QueryForm()
    
    context = {
        'form': form,
        'schema_info': schema_info,
        'schema_str': schema_str
    }
    
    return render(request, 'dashboard/query.html', context)


logger = logging.getLogger(__name__)

@login_required
@require_POST
def process_query(request):
    """Process a natural language query and convert to SQL"""
    form = QueryForm(request.POST)
    
    if form.is_valid():
        natural_language = form.cleaned_data['query']
        
        db_service = DatabaseService()
        llm_service = LLMService()
        
        # Get schema information for context
        schema_info, schema_str = db_service.get_schema_info()
        
        # Generate SQL using LLM
        try:
            sql_query = llm_service.generate_sql(natural_language, schema_str)
            
            # Execute SQL query
            result = db_service.execute_query(sql_query)
            
            # Save query to history
            query = Query.objects.create(
                user=request.user,
                natural_language=natural_language,
                sql_query=sql_query,
                result_json=result
            )
            
            # Log the generated SQL and result
            logger.info(f"Generated SQL: {sql_query}")
            logger.info(f"Query Result: {result}")
            
            # return JsonResponse({
            #     'success': True,
            #     'query_id': query.id,
            #     'sql': sql_query,
            #     'result': result
            # })
            return render(request, 'dashboard/query.html', {
                'form': form, 
                'schema_info': schema_info,
                'sql_query': sql_query,
            })
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid form data'
    })

def query_page(request):
    """Render the query page with the form and schema information"""
    form = QueryForm()
    db_service = DatabaseService()
    
    # Get schema information for the template
    schema_info, _ = db_service.get_schema_info()
    
    return render(request, 'dashboard/query.html', {
        'form': form,
        'schema_info': schema_info
    })

@login_required
def history_view(request):
    """View query history"""
    queries = Query.objects.filter(user=request.user)
    return render(request, 'dashboard/history.html', {'queries': queries})

@login_required
@require_POST
def save_feedback(request, query_id):
    """Save feedback for a query"""
    query = get_object_or_404(Query, id=query_id, user=request.user)
    form = QueryFeedbackForm(request.POST)
    
    if form.is_valid():
        rating = form.cleaned_data['rating']
        is_helpful = form.cleaned_data['is_helpful']
        comments = form.cleaned_data['comments']
        
        feedback, created = QueryFeedback.objects.update_or_create(
            query=query,
            defaults={
                'rating': rating,
                'is_helpful': is_helpful,
                'comments': comments
            }
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def export_csv(request, query_id):
    """Export query results as CSV"""
    query = get_object_or_404(Query, id=query_id, user=request.user)
    
    db_service = DatabaseService()
    csv_data = db_service.get_csv(query.sql_query)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="query_result_{query_id}.csv"'
    
    return response

@login_required
def rerun_query(request, query_id):
    """Re-run a previous query"""
    query = get_object_or_404(Query, id=query_id, user=request.user)
    
    db_service = DatabaseService()
    result = db_service.execute_query(query.sql_query)
    
    # Update the query with new results
    query.result_json = result
    query.save()
    
    return JsonResponse({
        'success': True,
        'query_id': query.id,
        'sql': query.sql_query,
        'result': result
    })