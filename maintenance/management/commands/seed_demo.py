from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from maintenance.models import (
    Asset,
    Category,
    InventoryItem,
    StockMovement,
    SubCategory,
    Ticket,
    TicketMedia,
    User,
)

DEMO_USERS = [
    {
        'username': 'superadmin',
        'password': 'IR@Super2026',
        'first_name': 'R.',
        'last_name': 'Mehta',
        'role': User.Role.SUPERADMIN,
        'employee_code': 'SA-001',
        'department': 'Reliability',
        'phone': 'Ext 2101',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'username': 'admin',
        'password': 'IR@Admin2026',
        'first_name': 'A.',
        'last_name': 'Iyer',
        'role': User.Role.ADMIN,
        'employee_code': 'ADM-101',
        'department': 'Maintenance',
        'phone': 'Ext 2210',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'admin2',
        'password': 'IR@Admin2026',
        'first_name': 'S.',
        'last_name': 'Khan',
        'role': User.Role.ADMIN,
        'employee_code': 'ADM-118',
        'department': 'Maintenance',
        'phone': 'Ext 2218',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'employee',
        'password': 'IR@User2026',
        'first_name': 'P.',
        'last_name': 'Desai',
        'role': User.Role.EMPLOYEE,
        'employee_code': 'EMP-221',
        'department': 'Assembly',
        'phone': 'Ext 3104',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'employee2',
        'password': 'IR@User2026',
        'first_name': 'N.',
        'last_name': 'Rao',
        'role': User.Role.EMPLOYEE,
        'employee_code': 'EMP-228',
        'department': 'Testing',
        'phone': 'Ext 3112',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'employee3',
        'password': 'IR@User2026',
        'first_name': 'K.',
        'last_name': 'Shah',
        'role': User.Role.EMPLOYEE,
        'employee_code': 'EMP-240',
        'department': 'Quality',
        'phone': 'Ext 3302',
        'is_staff': False,
        'is_superuser': False,
    },
]

# name, code, description, assets as (code, name, location)
CATALOG = [
    ('Centrifugal Pumps', 'CF', 'End-suction and process centrifugal pumps on test and assembly.', [
        ('Impeller Wear', 'CF-IMP', 'Vane wear, imbalance, or cavitation damage.', [('IR-CF-2214', 'Centrifugal Pump CP-2214', 'Assembly Line 2')]),
        ('Mechanical Seal Leak', 'CF-SEAL', 'Visible leak at the mechanical seal.', [('IR-CF-2208', 'Centrifugal Pump CP-2208', 'Test Bay 1')]),
        ('Bearing Failure', 'CF-BRG', 'Noise, heat, or play in the pump bearing.', [('IR-CF-2201', 'Centrifugal Pump CP-2201', 'Test Bay 1')]),
        ('Coupling Misalignment', 'CF-CPL', 'Hot coupling or a damaged spider.', [('IR-CF-2220', 'Centrifugal Pump CP-2220', 'Assembly Line 2')]),
        ('Casing Leak', 'CF-CASE', 'Weep or crack on the volute casing.', [('IR-CF-2233', 'Centrifugal Pump CP-2233', 'Dispatch Test')]),
        ('Shaft Sleeve Wear', 'CF-SLV', 'Scored sleeve under the packing or seal.', [('IR-CF-2240', 'Centrifugal Pump CP-2240', 'Overhaul Cell')]),
    ]),
    ('ARO Diaphragm Pumps', 'ARO', 'Air-operated double diaphragm pumps in fluid cells.', [
        ('Diaphragm Rupture', 'ARO-DIA', 'Product leaking through the air side.', [('IR-ARO-1104', 'ARO Diaphragm Pump 1104', 'Fluid Cell A')]),
        ('Air Valve Malfunction', 'ARO-AV', 'Pump will not shift or short-strokes.', [('IR-ARO-1119', 'ARO Diaphragm Pump 1119', 'Paint Shop')]),
        ('Check Ball Wear', 'ARO-BALL', 'Ball or seat no longer holding prime.', [('IR-ARO-1126', 'ARO Diaphragm Pump 1126', 'Fluid Cell B')]),
        ('Muffler Blockage', 'ARO-MUF', 'Icing or a choked exhaust muffler.', [('IR-ARO-1130', 'ARO Diaphragm Pump 1130', 'Paint Shop')]),
        ('Center Section Leak', 'ARO-CTR', 'Air leak at the center block.', [('IR-ARO-1142', 'ARO Diaphragm Pump 1142', 'Fluid Cell A')]),
    ]),
    ('Piston and Plunger Pumps', 'PST', 'High-pressure piston and plunger units.', [
        ('Packing Leak', 'PST-PKG', 'Packing will not hold pressure.', [('IR-PST-4407', 'Plunger Pump PP-4407', 'Hydraulics Room')]),
        ('Valve Seat Damage', 'PST-SEAT', 'Knock or loss of volumetric efficiency.', [('IR-PST-4415', 'Plunger Pump PP-4415', 'Hydraulics Room')]),
        ('Plunger Scoring', 'PST-PLN', 'Scored plunger or worn bushing.', [('IR-PST-4422', 'Plunger Pump PP-4422', 'Pump Test Lab')]),
        ('Lubrication Failure', 'PST-LUB', 'Crosshead or crankcase oil problem.', [('IR-PST-4430', 'Plunger Pump PP-4430', 'Pump Test Lab')]),
    ]),
    ('Progressive Cavity Pumps', 'PC', 'Progressive cavity pumps on process lines.', [
        ('Stator Wear', 'PC-STA', 'Stator no longer holding capacity.', [('IR-PD-3302', 'PC Pump PD-3302', 'Line 4')]),
        ('Rotor Damage', 'PC-ROT', 'Rotor wear or chrome breakdown.', [('IR-PD-3310', 'PC Pump PD-3310', 'Line 4')]),
        ('Joint Failure', 'PC-JNT', 'Drive joint or coupling failure.', [('IR-PD-3318', 'PC Pump PD-3318', 'Line 4')]),
        ('Dry Run Damage', 'PC-DRY', 'Pump ran dry and overheated.', [('IR-PD-3325', 'PC Pump PD-3325', 'Pilot Bay')]),
    ]),
    ('Drive Motors and Power', 'MTR', 'Motors and drives coupled to the pump.', [
        ('Overheating', 'MTR-HOT', 'Motor temperature above the limit.', [('IR-MTR-5510', 'Drive Motor 15 kW', 'Motor Bay')]),
        ('Vibration', 'MTR-VIB', 'High vibration on the drive end.', [('IR-MTR-5514', 'Drive Motor 30 kW', 'Compressor Room')]),
        ('Electrical Fault', 'MTR-ELC', 'Trip, earth fault, or winding alarm.', [('IR-MTR-5521', 'Drive Motor 7.5 kW', 'Assembly Line 2')]),
        ('VFD Alarm', 'MTR-VFD', 'Drive fault stopping the pump.', [('IR-MTR-5528', 'VFD Panel 5528', 'Compressor Room')]),
    ]),
    ('Sealing and Connections', 'SEL', 'Flanges, hoses, gaskets, and O-rings.', [
        ('Flange Leak', 'SEL-FLG', 'Leak at a suction or discharge flange.', [('IR-SEL-8102', 'Flange Set 8102', 'Pipe Rack A')]),
        ('Hose Burst', 'SEL-HOSE', 'Flexible hose failed under pressure.', [('IR-SEL-8110', 'Hose Assembly 8110', 'Fluid Cell A')]),
        ('O-Ring Failure', 'SEL-OR', 'O-ring cut, swollen, or missing.', [('IR-SEL-8116', 'Seal Kit Station', 'Overhaul Cell')]),
        ('Gasket Blowout', 'SEL-GSK', 'Gasket blown after a pressure test.', [('IR-SEL-8124', 'Gasket Joint 8124', 'Test Bay 1')]),
    ]),
    ('Lubrication Systems', 'LUB', 'Oil, filters, and lube skids.', [
        ('Oil Level Low', 'LUB-LVL', 'Sump or header level below the mark.', [('IR-LUB-6101', 'Lube Skid 6101', 'Utilities')]),
        ('Filter Clog', 'LUB-FLT', 'High differential across the oil filter.', [('IR-LUB-6108', 'Lube Filter 6108', 'Utilities')]),
        ('Lube Pump Failure', 'LUB-PMP', 'Circulation pump not building pressure.', [('IR-LUB-6115', 'Lube Pump 6115', 'Hydraulics Room')]),
        ('Oil Contamination', 'LUB-CNT', 'Water or particles in the oil.', [('IR-LUB-6122', 'Oil Sample Point', 'Utilities')]),
    ]),
    ('Instrumentation and Controls', 'INS', 'Sensors, meters, and safety circuits.', [
        ('Pressure Sensor Fault', 'INS-P', 'Pressure reading stuck or implausible.', [('IR-INS-7702', 'Pressure Sensor Bay 1', 'Test Bay 1')]),
        ('Flow Meter Drift', 'INS-F', 'Flow total no longer matches the curve.', [('IR-INS-7710', 'Flow Meter Line 4', 'Line 4')]),
        ('PLC Alarm', 'INS-PLC', 'Controller alarm holding the pump.', [('IR-INS-7718', 'PLC Cabinet', 'Control Room')]),
        ('Emergency Stop Fault', 'INS-ESTOP', 'E-stop loop open or not resetting.', [('IR-INS-7726', 'E-Stop Line 2', 'Assembly Line 2')]),
    ]),
]

PARTS = [
    ('MS-25', 'Mechanical Seal 25 mm', 'Drive-end mechanical seal for CP series.', 'pcs', 14, 14, 4, 'Cage A'),
    ('BRG-6205', 'Bearing 6205-2RS', 'Drive-end ball bearing.', 'pcs', 22, 22, 8, 'Cage A'),
    ('BRG-6308', 'Bearing 6308-2RS', 'Inboard ball bearing.', 'pcs', 6, 6, 4, 'Cage A'),
    ('IMP-CF-180', 'Impeller SS 180 mm', 'Stainless impeller for CP-2200 frame.', 'pcs', 3, 4, 2, 'Main Stores'),
    ('GSK-CF-200', 'Casing Gasket', 'Casing gasket for centrifugal overhaul.', 'pcs', 9, 10, 4, 'Main Stores'),
    ('DIA-PTFE-1', 'Diaphragm PTFE 1 inch', 'ARO PTFE diaphragm.', 'pcs', 18, 18, 6, 'Fluid Stores'),
    ('DIA-SANT-1', 'Diaphragm Santoprene 1 inch', 'ARO Santoprene diaphragm.', 'pcs', 2, 2, 6, 'Fluid Stores'),
    ('AV-ARO-M', 'Air Valve Assembly', 'Main air valve for ARO diaphragm pumps.', 'pcs', 7, 8, 3, 'Fluid Stores'),
    ('CB-NBR', 'Check Ball NBR', 'NBR check ball.', 'pcs', 40, 40, 15, 'Fluid Stores'),
    ('OR-KIT-A', 'O-Ring Kit Viton', 'Viton O-ring kit, pump frame A.', 'kit', 11, 11, 5, 'Cage B'),
    ('CPL-SP-L090', 'Coupling Spider L090', 'Elastomer spider for L090 coupling.', 'pcs', 4, 4, 3, 'Cage B'),
    ('SS-25', 'Shaft Sleeve 25 mm', 'Replaceable shaft sleeve.', 'pcs', 5, 5, 2, 'Cage A'),
    ('OIL-VG68', 'Hydraulic Oil VG 68', 'Circulating oil, issued in litres.', 'litre', 48, 53, 20, 'Consumables'),
    ('PKG-PST', 'Plunger Packing Set', 'Packing set for PP-4400 plunger pumps.', 'set', 1, 1, 4, 'Cage B'),
    ('STATOR-PC10', 'Stator NBR PC10', 'NBR stator for PC10 frame.', 'pcs', 2, 2, 1, 'Main Stores'),
    ('FLT-OIL-10', 'Oil Filter Element', 'Element for the lube skid.', 'pcs', 8, 9, 3, 'Consumables'),
    ('SENS-P16', 'Pressure Sensor 16 bar', 'Test-bay pressure transmitter.', 'pcs', 1, 1, 2, 'Cage B'),
    ('BOLT-M12', 'M12 Fastener Kit', 'Studs, nuts, and washers.', 'kit', 30, 30, 10, 'Consumables'),
]


class Command(BaseCommand):
    help = 'Load sample users, pump catalog, inventory, and maintenance jobs.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Rebuild sample catalog, stock, and jobs.')

    def handle(self, *args, **options):
        users = self._ensure_users(reset_passwords=options['reset'])
        if Category.objects.exists() and not options['reset']:
            self._logins()
            self.stdout.write('Demo catalog already loaded. Run with --reset to rebuild sample jobs.')
            return
        with transaction.atomic():
            if options['reset']:
                self._wipe()
            self._build(users)
        self._logins()
        self.stdout.write(self.style.SUCCESS('Sample plant data is ready.'))

    def _ensure_users(self, reset_passwords):
        people = {}
        for row in DEMO_USERS:
            data = dict(row)
            password = data.pop('password')
            try:
                user = User.objects.get(username=data['username'])
            except User.DoesNotExist:
                user = User(**data)
                user.set_password(password)
                user.save()
            else:
                if reset_passwords:
                    for key, value in data.items():
                        setattr(user, key, value)
                    user.set_password(password)
                    user.save()
            people[user.username] = user
        boss = people['superadmin']
        for username, user in people.items():
            if username != 'superadmin' and user.created_by_id != boss.id:
                user.created_by = boss
                user.save(update_fields=['created_by'])
        return people

    def _wipe(self):
        StockMovement.objects.all().delete()
        TicketMedia.objects.all().delete()
        Ticket.objects.all().delete()
        InventoryItem.objects.all().delete()
        Asset.objects.all().delete()
        SubCategory.objects.all().delete()
        Category.objects.all().delete()

    def _build(self, users):
        now = timezone.now()
        assets = {}
        for index, (name, code, description, subs) in enumerate(CATALOG, start=1):
            category = Category.objects.create(name=name, code=code, description=description, sort_order=index)
            for sub_index, (sub_name, sub_code, sub_desc, machines) in enumerate(subs, start=1):
                subcategory = SubCategory.objects.create(
                    category=category,
                    name=sub_name,
                    code=sub_code,
                    description=sub_desc,
                    sort_order=sub_index,
                )
                for asset_code, asset_name, location in machines:
                    asset = Asset.objects.create(
                        subcategory=subcategory,
                        code=asset_code,
                        name=asset_name,
                        location=location,
                    )
                    assets[asset_code] = asset

        counters = {}

        def ticket_no(when):
            key = timezone.localtime(when).strftime('%Y%m%d')
            counters[key] = counters.get(key, 0) + 1
            return f'IRM-{key}-{counters[key]:03d}'

        def make_ticket(*, asset_code, who, priority, status, remarks, created, actor=None, attempted=None, completed=None, attempt_notes='', completion_notes=''):
            asset = assets.get(asset_code)
            if asset is None:
                raise CommandError(f'Missing sample machine {asset_code}')
            return Ticket.objects.create(
                ticket_no=ticket_no(created),
                raised_by=who,
                asset=asset,
                category=asset.subcategory.category,
                subcategory=asset.subcategory,
                priority=priority,
                status=status,
                remarks=remarks,
                created_at=created,
                attempted_at=attempted,
                attempted_by=actor if attempted else None,
                attempt_notes=attempt_notes,
                completed_at=completed,
                completed_by=actor if completed else None,
                completion_notes=completion_notes,
            )

        emp = users['employee']
        emp2 = users['employee2']
        emp3 = users['employee3']
        admin = users['admin']
        admin2 = users['admin2']

        make_ticket(
            asset_code='IR-ARO-1104',
            who=emp,
            priority=Ticket.Priority.CRITICAL,
            status=Ticket.Status.PENDING,
            remarks='Product is coming out of the air side after shift start. Pump is stopped and the skid is wet.',
            created=now - timedelta(minutes=26),
        )
        make_ticket(
            asset_code='IR-CF-2208',
            who=emp2,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.PENDING,
            remarks='Seal weepage became a steady drip at the drive end during the pressure test. Machine is isolated.',
            created=now - timedelta(hours=2, minutes=15),
        )
        make_ticket(
            asset_code='IR-INS-7702',
            who=emp3,
            priority=Ticket.Priority.LOW,
            status=Ticket.Status.PENDING,
            remarks='Pressure reading is stuck at zero on the test bay gauge. The run was aborted.',
            created=now - timedelta(minutes=40),
        )
        make_ticket(
            asset_code='IR-CF-2201',
            who=emp,
            priority=Ticket.Priority.MEDIUM,
            status=Ticket.Status.ATTEMPTED,
            remarks='Growling noise from the drive-end bearing. Pump taken off test.',
            created=now - timedelta(hours=7),
            attempted=now - timedelta(hours=5),
            actor=admin,
            attempt_notes='Housing is open. Bearing feels rough. Fitment is next.',
        )
        make_ticket(
            asset_code='IR-CF-2220',
            who=emp2,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.ATTEMPTED,
            remarks='Coupling ran hot and the spider is shredded. Assembly Line 2 pump is down.',
            created=now - timedelta(hours=26),
            attempted=now - timedelta(hours=3),
            actor=admin2,
            attempt_notes='Guard is off. Alignment is out. Spider still to be fitted.',
        )
        make_ticket(
            asset_code='IR-PST-4407',
            who=emp3,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.ATTEMPTED,
            remarks='Packing will not hold. Score marks visible on the sleeve area.',
            created=now - timedelta(hours=5),
            attempted=now - timedelta(hours=2),
            actor=admin,
            attempt_notes='Packing pulled. Measuring the replacement set.',
        )

        impeller_created = now - timedelta(hours=46)
        impeller_done = now - timedelta(hours=28)
        impeller = make_ticket(
            asset_code='IR-CF-2214',
            who=emp,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.COMPLETED,
            remarks='Vibration was high. Impeller vanes are worn and out of balance.',
            created=impeller_created,
            attempted=now - timedelta(hours=40),
            completed=impeller_done,
            actor=admin,
            attempt_notes='Pump stripped. Impeller confirmed damaged.',
            completion_notes='Impeller and casing gasket replaced. Vibration is back in limit. Pump returned to test.',
        )
        valve_done = now - timedelta(hours=16, minutes=20)
        valve = make_ticket(
            asset_code='IR-ARO-1119',
            who=emp2,
            priority=Ticket.Priority.MEDIUM,
            status=Ticket.Status.COMPLETED,
            remarks='Pump cycles but will not shift. Air valve suspected.',
            created=now - timedelta(hours=20),
            attempted=now - timedelta(hours=18),
            completed=valve_done,
            actor=admin2,
            attempt_notes='Muffler clear. Air valve sticking.',
            completion_notes='Air valve assembly replaced. Pump shifts normally and is back in service.',
        )
        lube_done = now - timedelta(hours=5, minutes=8)
        lube = make_ticket(
            asset_code='IR-LUB-6101',
            who=emp3,
            priority=Ticket.Priority.MEDIUM,
            status=Ticket.Status.COMPLETED,
            remarks='Oil pressure light on the lube skid. Filter differential is high.',
            created=now - timedelta(hours=6),
            attempted=now - timedelta(hours=5, minutes=30),
            completed=lube_done,
            actor=admin,
            attempt_notes='Element is collapsed. Oil is low as well.',
            completion_notes='Filter element replaced and 5 litres topped up. Pressure is normal.',
        )

        opened = now - timedelta(days=30)
        items = {}
        for sku, name, description, unit, quantity, opening, minimum, location in PARTS:
            item = InventoryItem.objects.create(
                sku=sku,
                name=name,
                description=description,
                unit=unit,
                quantity=quantity,
                min_quantity=minimum,
                location=location,
            )
            StockMovement.objects.create(
                item=item,
                quantity_change=opening,
                balance_after=opening,
                reason=StockMovement.Reason.RECEIPT,
                note='Opening balance',
                created_by=admin,
                created_at=opened,
            )
            items[sku] = item

        def issue(sku, qty, balance, ticket, when, actor, note):
            StockMovement.objects.create(
                item=items[sku],
                ticket=ticket,
                quantity_change=-qty,
                balance_after=balance,
                reason=StockMovement.Reason.JOB,
                note=note,
                created_by=actor,
                created_at=when,
            )

        issue('IMP-CF-180', 1, 3, impeller, impeller_done - timedelta(minutes=25), admin, 'Impeller fitted on CP-2214')
        issue('GSK-CF-200', 1, 9, impeller, impeller_done - timedelta(minutes=20), admin, 'Casing gasket fitted')
        issue('AV-ARO-M', 1, 7, valve, valve_done - timedelta(minutes=15), admin2, 'Air valve replaced on 1119')
        issue('FLT-OIL-10', 1, 8, lube, lube_done - timedelta(minutes=12), admin, 'Filter element changed')
        issue('OIL-VG68', 5, 48, lube, lube_done - timedelta(minutes=8), admin, 'Top-up, 5 litres')

    def _logins(self):
        self.stdout.write('')
        self.stdout.write('Sign in at http://127.0.0.1:8000/')
        self.stdout.write('Super Admin   superadmin / IR@Super2026')
        self.stdout.write('Admin         admin      / IR@Admin2026')
        self.stdout.write('Employee      employee   / IR@User2026')
        self.stdout.write('Live board    /board/    after signing in as admin')
        self.stdout.write('')
