from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .decorators import role_required
from .forms import ParcelForm, TrackingUpdateForm
from .models import Branch, Parcel, Payment, TrackingEvent
from .roles import role_names


class StaffLoginView(LoginView):
    """Send customers to public pages and authorized operations users to staff."""
    def get_success_url(self):
        if self.request.user.has_perm("operations.view_parcel"):
            return reverse("dashboard")
        return reverse("home")


class StaffUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=[(name, name) for name in role_names()])

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data["role"]
        user.is_staff = role != "Customer"
        if commit:
            user.save()
            user.groups.set([Group.objects.get(name=role)])
        return user


def home(request):
    return render(request, "operations/home.html")


def about(request):
    return render(request, "operations/about.html")


def services(request):
    return render(request, "operations/services.html")


def branches(request):
    locations = Branch.objects.filter(is_active=True).order_by("name")
    return render(request, "operations/branches.html", {"branches": locations})


def contact(request):
    return render(request, "operations/contact.html")


def track_parcel(request):
    parcel, searched = None, False
    if request.method == "POST":
        searched = True
        code = request.POST.get("tracking_number", "").strip().upper()
        if code:
            parcel = Parcel.objects.filter(tracking_number=code).first()
    return render(request, "operations/track.html", {"parcel": parcel, "searched": searched})


@login_required
@permission_required("operations.view_parcel", raise_exception=True)
def dashboard(request):
    counts = {
        "total": Parcel.objects.count(),
        "in_transit": Parcel.objects.filter(status=Parcel.Status.IN_TRANSIT).count(),
        "collected": Parcel.objects.filter(status=Parcel.Status.COLLECTED).count(),
        "pending": Parcel.objects.filter(status__in=[
            Parcel.Status.PAYMENT_PENDING,
            Parcel.Status.READY_DISPATCH,
            Parcel.Status.READY_COLLECTION,
        ]).count(),
    }
    if request.user.has_perm("operations.view_payment"):
        counts["revenue"] = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    recent = Parcel.objects.select_related("sender", "recipient", "origin", "destination").order_by("-created_at")[:8]
    return render(request, "operations/dashboard.html", {
        "counts": counts,
        "recent_parcels": recent,
        "can_register_parcels": request.user.has_perm("operations.add_parcel"),
    })


@login_required
@permission_required("operations.view_parcel", raise_exception=True)
def parcel_list(request):
    parcels = Parcel.objects.select_related("sender", "recipient", "origin", "destination").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    if query:
        parcels = parcels.filter(tracking_number__icontains=query)
    return render(request, "operations/parcel_list.html", {"parcels": parcels[:100], "query": query})


@login_required
@permission_required("operations.add_parcel", raise_exception=True)
def parcel_create(request):
    form = ParcelForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            parcel = form.save()
            TrackingEvent.objects.create(
                parcel=parcel,
                status=parcel.status,
                location=parcel.origin.name,
                note="Parcel registered",
                created_by=request.user,
            )
        messages.success(request, f"Parcel registered. Tracking code: {parcel.tracking_number}")
        return redirect("parcel_detail", pk=parcel.pk)
    return render(request, "operations/parcel_form.html", {"form": form})


@login_required
@permission_required("operations.view_parcel", raise_exception=True)
def parcel_detail(request, pk):
    parcel = get_object_or_404(
        Parcel.objects.select_related("sender", "recipient", "origin", "destination"),
        pk=pk,
    )
    can_update_tracking = request.user.is_superuser or request.user.groups.filter(
        name__in=["System Administrator", "Branch Manager", "Dispatcher"]
    ).exists()
    return render(request, "operations/parcel_detail.html", {
        "parcel": parcel,
        "events": parcel.tracking_events.select_related("created_by"),
        "tracking_form": TrackingUpdateForm(initial={"status": parcel.status}),
        "can_update_tracking": can_update_tracking,
    })
@login_required
@role_required("System Administrator", "Branch Manager", "Dispatcher")
def update_status(request, pk):
    if request.method != "POST":
        raise PermissionDenied("Parcel status changes must use POST.")
    parcel = get_object_or_404(Parcel, pk=pk)
    form = TrackingUpdateForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please correct the tracking update and try again.")
    elif form.cleaned_data["status"] == parcel.status:
        messages.info(request, "Parcel already has that status. No duplicate event was added.")
    else:
        with transaction.atomic():
            parcel.status = form.cleaned_data["status"]
            parcel.save(update_fields=["status", "updated_at"])
            TrackingEvent.objects.create(
                parcel=parcel,
                status=parcel.status,
                location=form.cleaned_data["location"],
                note=form.cleaned_data["note"],
                created_by=request.user,
            )
        messages.success(request, "Parcel status and tracking history updated.")
    return redirect("parcel_detail", pk=parcel.pk)
@login_required
@role_required("System Administrator", "Branch Manager")
def management_dashboard(request):
    context = {
        "branch_count": Branch.objects.filter(is_active=True).count(),
        "branches": Branch.objects.annotate(parcel_count=Count("origin_parcels")).order_by("name"),
        "can_view_finance": request.user.has_perm("operations.view_payment"),
    }
    if context["can_view_finance"]:
        context["recorded_revenue"] = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    return render(request, "operations/management_dashboard.html", context)


@login_required
@role_required("System Administrator")
def staff_users(request):
    users = get_user_model().objects.prefetch_related("groups").order_by("username")
    return render(request, "operations/staff_users.html", {"staff_users": users})


@login_required
@role_required("System Administrator")
def staff_user_create(request):
    form = StaffUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Account {user.username} created with the {form.cleaned_data['role']} role.")
        return redirect("staff_users")
    return render(request, "operations/staff_user_form.html", {"form": form})
