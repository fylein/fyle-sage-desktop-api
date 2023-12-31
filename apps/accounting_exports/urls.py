"""sage_desktop_api URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from .views import AccountingExportView, ErrorsView, AccountingExportCountView, AccountingExportSummaryView


urlpatterns = [
    path('', AccountingExportView.as_view(), name='accounting-exports'),
    path('count/', AccountingExportCountView.as_view(), name='accounting-exports-count'),
    path('summary/', AccountingExportSummaryView.as_view(), name='accounting-exports-summary'),
    path('errors/', ErrorsView.as_view(), name='errors'),
]
