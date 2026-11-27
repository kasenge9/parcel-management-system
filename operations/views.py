from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ParcelForm
from .models import Parcel, Payment, TrackingEvent


def home(request):
    return render(request, "operations/home.html")


def about(request):
    return render(request, "operations/about.html")


def services(request):
    return render(request, "operations/services.html")


def track_parcel(request):
    parcel, searched = None, False
    if request.method == "POST":
        searched = True
        code = request.POST.get("tracking_number", "").strip().upper()
        if code:
            parcel = Parcel.objects.filter(tracking_number=code).first()
    return render(request, "operations/track.html", {"parcel": parcel, "searched": searched})


@login_required
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
    counts["revenue"] = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    recent = Parcel.objects.select_related("sender", "recipient", "origin", "destination").order_by("-created_at")[:8]
    return render(request, "operations/dashboard.html", {"counts": counts, "recent_parcels": recent})


@login_required
def parcel_list(request):
    parcels = Parcel.objects.select_related("sender", "recipient", "origin", "destination").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    if query:
        parcels = parcels.filter(tracking_number__icontains=query)
    return render(request, "operations/parcel_list.html", {"parcels": parcels[:100], "query": query})


@login_required
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
def parcel_detail(request, pk):
    parcel = get_object_or_404(
        Parcel.objects.select_related("sender", "recipient", "origin", "destination"),
        pk=pk,
    )
    return render(request, "operations/parcel_detail.html", {
        "parcel": parcel,
        "events": parcel.tracking_events.select_related("created_by"),
    })


@login_required
def update_status(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk)
    if request.method == "POST":
        status = request.POST.get("status", "")
        allowed = {value for value, _ in Parcel.Status.choices}
        if status not in allowed:
            messages.error(request, "Choose a valid parcel status.")
        elif status == parcel.status:
            messages.info(request, "Parcel already has that status.")
        else:
            with transaction.atomic():
                parcel.status = status
                parcel.save(update_fields=["status", "updated_at"])
                location = parcel.destination.name if status in {
                    Parcel.Status.ARRIVED,
                    Parcel.Status.READY_COLLECTION,
                    Parcel.Status.COLLECTED,
                } else ""
                TrackingEvent.objects.create(
                    parcel=parcel,
                    status=status,
                    location=location,
                    created_by=request.user,
                )
            messages.success(request, "Status and tracking history updated.")
    return redirect("parcel_detail", pk=parcel.pk)
