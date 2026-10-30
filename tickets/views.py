from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .forms import CommentForm, RegisterForm, TicketForm
from .models import Ticket


def is_it_staff(user):
    return user.is_authenticated and user.role == "staff"


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def ticket_list(request):
    tickets = Ticket.objects.select_related("author", "assignee")
    if not is_it_staff(request.user):
        tickets = tickets.filter(author=request.user)

    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    if status in Ticket.Status.values:
        tickets = tickets.filter(status=status)
    if q:
        tickets = tickets.filter(title__icontains=q)

    page = Paginator(tickets, 10).get_page(request.GET.get("page"))
    context = {"page": page, "status": status, "q": q, "statuses": Ticket.Status.choices}
    return render(request, "tickets/ticket_list.html", context)


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.author = request.user
            ticket.save()
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, "tickets/ticket_form.html", {"form": form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if ticket.author != request.user and not is_it_staff(request.user):
        raise PermissionDenied

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            if is_ajax:
                html = render_to_string("tickets/_comment.html", {"c": comment}, request=request)
                return JsonResponse({"ok": True, "html": html})
            return redirect("ticket_detail", pk=ticket.pk)
        if is_ajax:
            error = form.errors["text"][0] if "text" in form.errors else "Проверьте текст комментария."
            return JsonResponse({"ok": False, "error": error}, status=400)
    else:
        form = CommentForm()

    return render(request, "tickets/ticket_detail.html", {"ticket": ticket, "form": form})


@login_required
@require_POST
def ticket_status(request, pk):
    if not is_it_staff(request.user):
        raise PermissionDenied
    ticket = get_object_or_404(Ticket, pk=pk)
    new_status = request.POST.get("status", "")
    if not ticket.can_change_status_to(new_status):
        messages.error(request, "Такой переход статуса запрещён.")
    else:
        ticket.status = new_status
        if new_status == Ticket.Status.IN_PROGRESS:
            ticket.assignee = request.user
        ticket.save()
        messages.success(request, "Статус обновлён.")
    return redirect("ticket_detail", pk=ticket.pk)