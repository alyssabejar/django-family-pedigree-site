import json
import os
import requests
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic.base import View
from rest_framework.reverse import reverse, reverse_lazy


api_url = os.getenv('API_URL')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
grant_type = os.getenv('GRANT_TYPE')
client_user = os.getenv('CLIENT_USER')
client_password = os.getenv('CLIENT_PASSWORD')


class HomeView(View):
    template_name = "home.html"

    def get(self, request):
        return is_authenticated(request, self.template_name)


def index_view(request):
    return redirect("home")


def login_view(request):
    # Function to use for User login requests.
    # Automatically redirects to HomeView() on success.
    template_name = "sign-in.html"
    error_message = None

    # Check for existing User session.
    user = request.session.get("USER")
    if user:
        return index_view(request)

    # If no existing User session, proceed to default.
    if request.method == "POST":
        request_body = request.POST
        username = request.session["SAVED_USERNAME"] = request_body.get('username')
        email = request_body.get('email')
        password = request_body.get('password')

        url = "{}/api/v1/users/get_user/".format(api_url)
        headers = construct_headers(request)
        payload = {
            "username": username,
            "email": email,
            "password": password,

        }

        resource = requests.post(url, json=payload, headers=headers)
        resource_data = resource.json()

        if resource.status_code == 200:
            user = request.session["USER"] = resource_data
            if user:
                return redirect("home")

        else:
            status_code = resource_data.get("status")
            error_message = resource_data.get("message")

    saved_username = request.session.get("SAVED_USERNAME") or ''

    return render(
        request,
        template_name,
        context={
            "saved_username": saved_username,
            "error_message": error_message,
        }
    )


def sign_up_view(request):
    # Function to use for User sign-up requests.
    # Automatically redirects to HomeView() on success.

    error_message = None
    cached_form = {
        "username": '',
        "email": '',
        "first_name": '',
        "last_name": '',
    }

    # Check for existing User session.
    user = request.session.get("USER")
    if user:
        return index_view(request)

    # If no existing User session, proceed to default.
    if request.method == "POST":
        request_body = request.POST
        username = request_body.get('username')
        email = request_body.get('email')
        password1 = request_body.get('password1')
        password2 = request_body.get('password2')
        first_name = request_body.get('first_name')
        last_name = request_body.get('last_name')
        dob = request_body.get('dob')
        relationship = request_body.get('relationship')
        vital_status = request_body.get('vital_status')

        cached_form = request.session["SAVED_SIGNUP_FORM"] = {
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
        }

        if password1 != password2:
            error_message = "ERROR: Passwords do not match."
            return render(
                request,
                template_name="sign-up.html",
                context={
                    "cached_form": cached_form,
                    "error_message": error_message,
                }
            )

        url = "{}/api/v1/users/create_user/".format(api_url)
        headers = construct_headers(request)
        payload = {
            "username": username,
            "email": email,
            "password": password1,
            "first_name": first_name,
            "last_name": last_name,
            "relationship": relationship,
            "vital_status": vital_status,
        }

        resource = requests.post(url, json=payload, headers=headers)
        resource_data = resource.json()

        if resource.status_code == 200:
            user = request.session["USER"] = resource_data
            account = create_account(request, user)
            member = add_member_view(request)
            return redirect("home")

        else:
            status_code = resource_data.get("status")
            error_message = resource_data.get("message")

    return render(
        request,
        template_name="sign-up.html",
        context={
            "cached_form": cached_form,
            "error_message": error_message,
        }
    )


def logout_view(request):
    # Function to use for properly logging out.
    # Removes all session data using .flush()
    request.session.flush()
    return redirect("login")


def authenticate(request):
    # This function is used for requesting an access token.
    # The access token is then stored in the browser session for later use.
    # Returns a string.

    url = "{}/o/token/".format(api_url)

    payload = {
        "grant_type": grant_type,
        "username": client_user,
        "password": client_password,
    }

    auth = (client_id, client_secret)

    resource = requests.post(url, json=payload, auth=auth)
    resource_data = resource.json()

    request.session["API_SESSION"] = resource_data
    access_token = request.session["API_SESSION"]["access_token"]

    return access_token


def is_authenticated(request, redirect_to_template):
    # Function to check for existing User session.
    # If User session is valid, retrieves the User Account from user_id.
    # Automatically redirects to login view if no User session is found.

    user = request.session.get("USER")
    if user:
        account = request.session["ACCOUNT"] = get_account_from_user_id(request, user)
        context = {"account": account}
        return render(request, template_name=redirect_to_template, context=context)
    else:
        return redirect("login")


def get_account_from_user_id(request, user):
    # Function to retrieve an Account.
    # Requires a 'request' object and a 'user' object.
    # Returns a dict object, containing the Account details.

    url = "{}/api/v1/accounts/get_account_from_user_id/".format(api_url)
    headers = construct_headers(request)
    payload = {
        "user_id": user.get('id'),
    }

    resource = requests.post(url, json=payload, headers=headers)
    account = resource.json()

    return account


def create_account(request, user):
    # Function to create an Account.
    # Requires a 'request' object and a 'user' object.
    # Returns a dict object, containing the Account details.

    request_body = request.POST
    dob = request_body.get('dob')
    account = None

    if user:
        url = "{}/api/v1/accounts/create_account/".format(api_url)
        headers = construct_headers(request)
        payload = {
            "user_id": user.get('id'),
            "dob": dob,
        }

        resource = requests.post(url, json=payload, headers=headers)
        account = resource.json()

    return account


def create_member(request, user):
    # Function to create an Member.
    # Requires a 'request' object and a 'user' object.
    # Returns a dict object, containing the Member details.

    member = None

    if request.method == "POST":
        request_body = request.POST
        first_name = request_body.get('first_name')
        last_name = request_body.get('last_name')
        vital_status = request_body.get('vital_status')
        relationship = request_body.get('relationship')
        dob = request_body.get('dob')
        user = request.session.get('USER')

        url = "{}/api/v1/members/".format(api_url)
        headers = construct_headers(request)
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "vital_status": vital_status,
            "dob": dob,
            "relationship": relationship,
            "user": user['id'],
        }

        resource = requests.post(url, json=payload, headers=headers)
        resource_data = resource.json()

    return member


def add_member_view(request):
    # Function to create a family member.
    # Requires a 'request' object
    error_message = None
    status_code = None
    context = {}
    template_name = "add_member.html"

    if request.method == "POST":
        request_body = request.POST
        first_name = request_body.get('first_name')
        last_name = request_body.get('last_name')
        vital_status = request_body.get('vital_status')
        relationship = request_body.get('relationship')
        dob = request_body.get('dob')
        user = request.session.get('USER')

        url = "{}/api/v1/members/".format(api_url)
        headers = construct_headers(request)
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "vital_status": vital_status,
            "dob": dob,
            "relationship": relationship,
            "user": user['id'],
        }

        resource = requests.post(url, json=payload, headers=headers)
        resource_data = resource.json()

        if resource.status_code == 200:
            return redirect("home")
        else:
            context['status_code'] = resource_data.get("status")
            messages.error(request, resource_data.get("message"))

    return render(request, template_name, context)


def update_user_account_view(request, pk):
    # Function to update user account.
    # Requires a 'request' object and pk
    error_message = None
    context = {}
    template_name = "update_user_account.html"

    url = "{}/api/v1/user-account/{pk}/".format(api_url, pk=pk)
    headers = construct_headers(request)

    resource = requests.get(url, headers=headers)
    response = resource.json()

    if resource.status_code == 200:
        context['accounts'] = response
    else:
        context['status_code'] = response.get("status")
        messages.error(request, response.get("message"))
        return redirect("home")

    if request.method == "POST":
        request_body = request.POST
        first_name = request_body.get('first_name')
        last_name = request_body.get('last_name')
        dob = request_body.get('dob')
        email = request_body.get('email')

        update_url = "{}/api/v1/user-account/{pk}/".format(api_url, pk=pk)
        headers = construct_headers(request)

        data = {
            "dob": dob,
            "user": {
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        }

        resource_updated = requests.put(update_url, json=data, headers=headers)
        resource_updated_response = resource_updated.json()

        if resource_updated.status_code == 200:
            context['accounts'] = resource_updated_response
            return redirect("home")
        else:
            context['status_code'] = resource_updated_response.get("status")
            messages.error(request, resource_updated_response.get("message"))

    return render(request, template_name, context, )


def update_member_view(request, pk):
    # Function to update details of a family member.
    # Requires a 'request' object
    error_message = None
    context = {}
    template_name = "update_member.html"

    url = "{}/api/v1/members/{pk}/".format(api_url, pk=pk)
    headers = construct_headers(request)

    resource = requests.get(url, headers=headers)
    response = resource.json()

    if resource.status_code == 200:
        context['members'] = response
    else:
        context['status_code'] = response.get("status")
        messages.error(request, response.get("message"))
        return redirect("home")

    if request.method == "POST":
        request_body = request.POST
        first_name = request_body.get('first_name')
        last_name = request_body.get('last_name')
        vital_status = request_body.get('vital_status')
        relationship = request_body.get('relationship')
        dob = request_body.get('dob')
        user = request.session.get('USER')

        update_url = "{}/api/v1/members/{pk}/".format(api_url, pk=pk)
        headers = construct_headers(request)

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "vital_status": vital_status,
            "dob": dob,
            "relationship": relationship,
            "user": user['id'],
        }

        resource_updated = requests.put(update_url, data=data, headers=headers)
        resource_updated_response = resource_updated.json()

        if resource_updated.status_code == 200:
            context['member'] = resource_updated_response
            return redirect("home")
        else:
            context['status_code'] = resource_updated_response.get("status")
            messages.error(request, resource_updated_response.get("message"))
            return redirect("home")
    return render(request, template_name, context, )


def delete_member_view(request, pk):
    # Function to update details of a family member.
    # Requires a 'request' object
    error_message = None
    context = {}
    template_name = "delete_member.html"

    user = request.session.get('USER')
    url = "{}/api/v1/members/{pk}/".format(api_url, pk=pk)
    headers = construct_headers(request)

    resource = requests.get(url, headers=headers)
    response = resource.json()

    if resource.status_code == 200:
        context['members'] = response
        member = context['members']
    else:
        context['status_code'] = response.get("status")
        context['error_message'] = response.get("message")
        return redirect("home")

    # get user full name and member full name to be deleted
    member_fullname = member['first_name'] + member['last_name']
    user_fullname = user['first_name'] + user['last_name']
    if request.method == "POST":
        url = "{}/api/v1/members/{pk}/".format(api_url, pk=pk)
        headers = construct_headers(request)

        # restriction of deleting user's own member details
        if user_fullname != member_fullname:
            resource = requests.delete(url, headers=headers)
            return redirect("home")
        elif user_fullname == member_fullname:
            messages.error(request, "Cannot delete yourself as a member of the family")
            return redirect("home")
        else:
            context['status_code'] = 200
            messages.error(request, "Error encountered. Please try again")
            return redirect("home")

    return render(request, template_name, context)


def construct_headers(request):
    # Helper function to create an authorization header for API requests.
    # Checks the browser session for an existing access token.
    # If no access token is found, calls 'authenticate()' function to request for a new one.
    # Returns a dict object, containing the access token.

    access_token = None
    api_session = request.session.get("API_SESSION")

    if api_session:
        access_token = api_session.get("access_token")

    if not access_token:
        access_token = authenticate(request)

    return {"Authorization": "Bearer " + access_token}
