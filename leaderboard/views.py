from django.shortcuts import render

# Create your views here.
def landing_page(request):
    return render(request, "landing.html")

def about(request):
    return render(request,"about.html")
def register(request):
    return render(request,"register.html")

def login(request):
    return render(request,"login.html")
