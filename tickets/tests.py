from django.test import TestCase
from django.urls import reverse

from .models import Ticket, User

PASSWORD = "Pass12345"


class TicketTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("student1", password=PASSWORD)
        self.other = User.objects.create_user("student2", password=PASSWORD)
        self.staff = User.objects.create_user("staff1", password=PASSWORD, role=User.Role.STAFF)
        self.ticket = Ticket.objects.create(
            title="Не работает проектор",
            description="Нет изображения",
            room="204",
            author=self.student,
        )

    def status_url(self):
        return reverse("ticket_status", args=[self.ticket.pk])

    # 1. Права доступа
    def test_student_cannot_open_foreign_ticket(self):
        self.client.login(username="student2", password=PASSWORD)
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_change_status(self):
        self.client.login(username="student1", password=PASSWORD)
        response = self.client.post(self.status_url(), {"status": "in_progress"})
        self.assertEqual(response.status_code, 403)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.NEW)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("ticket_list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('ticket_list')}")

    # 2. Валидация
    def test_empty_title_is_rejected(self):
        self.client.login(username="student1", password=PASSWORD)
        response = self.client.post(
            reverse("ticket_create"),
            {"title": "", "description": "Текст", "room": "101", "priority": "low"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Ticket.objects.count(), 1)  # только заявка из setUp

    # 3. Основной успешный сценарий
    def test_student_creates_ticket(self):
        self.client.login(username="student1", password=PASSWORD)
        response = self.client.post(
            reverse("ticket_create"),
            {"title": "Нет интернета", "description": "Не грузятся сайты", "room": "315", "priority": "high"},
        )
        ticket = Ticket.objects.get(title="Нет интернета")
        self.assertRedirects(response, reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual(ticket.author, self.student)
        self.assertEqual(ticket.status, Ticket.Status.NEW)

    def test_staff_workflow_sets_assignee(self):
        self.client.login(username="staff1", password=PASSWORD)
        self.client.post(self.status_url(), {"status": "in_progress"})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(self.ticket.assignee, self.staff)

        self.client.post(self.status_url(), {"status": "resolved"})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.RESOLVED)

    # 4. Запрещённый переход статуса
    def test_forbidden_status_jump(self):
        self.client.login(username="staff1", password=PASSWORD)
        self.client.post(self.status_url(), {"status": "resolved"})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.NEW)

    # 5. Пограничные случаи
    def test_resolved_ticket_cannot_be_reopened(self):
        self.ticket.status = Ticket.Status.RESOLVED
        self.ticket.save()
        self.client.login(username="staff1", password=PASSWORD)
        self.client.post(self.status_url(), {"status": "new"})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.RESOLVED)

    def test_student_sees_only_own_tickets(self):
        Ticket.objects.create(
            title="Чужая заявка", description="Текст", room="1", author=self.other
        )
        self.client.login(username="student1", password=PASSWORD)
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "Не работает проектор")
        self.assertNotContains(response, "Чужая заявка")

    def test_registration_always_creates_student(self):
        self.client.post(
            reverse("register"),
            {
                "username": "newbie",
                "password1": "Zq7-mTest-pass",
                "password2": "Zq7-mTest-pass",
                "role": "staff",
            },
        )
        user = User.objects.get(username="newbie")
        self.assertEqual(user.role, User.Role.STUDENT)