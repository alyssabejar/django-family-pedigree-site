import debug_toolbar

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from client_site_users.views import (
    HomeView,
    login_view,
    sign_up_view,
    logout_view,
    index_view,

    update_user_account_view,

    add_member_view,
    update_member_view,
    delete_member_view
)


from .settings import STATIC_URL, STATIC_ROOT

urlpatterns = [
    path('', index_view, name="index"),
    path("login/", login_view, name="login"),
    path("sign_up/", sign_up_view, name="sign-up"),
    path("logout/", logout_view, name="logout"),
    path('home/', HomeView.as_view(), name="home"),

    path("account/update/<int:pk>/", update_user_account_view, name="user-account-detail"),

    path('members/', add_member_view, name="add-member"),
    path('members/update/<int:pk>/', update_member_view, name="members-detail"),
    path('members/delete/<int:pk>/', delete_member_view, name="members-delete"),

    path('admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
]

urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)