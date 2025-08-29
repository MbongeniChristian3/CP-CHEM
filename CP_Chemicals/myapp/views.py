from django.http import HttpResponse

def home(request):
    """
    A simple view function that returns an HTTP response with a greeting.
    This function will be called when a user navigates to the root URL.
    """
    return HttpResponse("Hello, World! Welcome to the  CP Chemicals Order Management System Development.")