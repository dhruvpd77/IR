from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from maintenance.models import Asset, Category, InventoryItem, StockMovement, SubCategory, Ticket
from maintenance.services import apply_stock_change

User = get_user_model()


class StockAndRoleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='adm', password='pass12345', role=User.Role.ADMIN)
        self.employee = User.objects.create_user(username='emp', password='pass12345', role=User.Role.EMPLOYEE)
        self.item = InventoryItem.objects.create(sku='X1', name='Seal', unit='pcs', quantity=2, min_quantity=1, location='A')
        category = Category.objects.create(name='Pumps', code='P')
        sub = SubCategory.objects.create(category=category, name='Seal', code='P-S')
        self.asset = Asset.objects.create(subcategory=sub, code='IR-1', name='Pump 1', location='Bay')

    def test_stock_cannot_go_negative(self):
        with self.assertRaises(ValueError):
            apply_stock_change(item=self.item, quantity_change=-3, reason=StockMovement.Reason.ADJUST, user=self.admin)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)

    def test_issue_updates_quantity(self):
        apply_stock_change(item=self.item, quantity_change=-1, reason=StockMovement.Reason.JOB, user=self.admin)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_employee_cannot_open_inventory(self):
        self.client.login(username='emp', password='pass12345')
        response = self.client.get(reverse('inventory_list'))
        self.assertEqual(response.status_code, 403)

    def test_complete_requires_attempt(self):
        ticket = Ticket.objects.create(
            ticket_no='IRM-TEST-001',
            raised_by=self.employee,
            asset=self.asset,
            category=self.asset.subcategory.category,
            subcategory=self.asset.subcategory,
            remarks='Seal is dripping on the test bay floor.',
        )
        self.client.login(username='adm', password='pass12345')
        response = self.client.post(reverse('ticket_complete', args=[ticket.pk]), {'completion_notes': 'Done and running again.'})
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.PENDING)
        self.assertIsNone(ticket.idle_delta)
        self.client.post(reverse('ticket_attempt', args=[ticket.pk]), {'attempt_notes': 'On the machine.'})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.ATTEMPTED)
        self.assertIsNotNone(ticket.idle_delta)
        self.client.post(reverse('ticket_complete', args=[ticket.pk]), {'completion_notes': 'Seal replaced and running.'})
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.COMPLETED)
        self.assertIsNotNone(ticket.completed_at)
        self.assertIsNotNone(ticket.idle_delta)
