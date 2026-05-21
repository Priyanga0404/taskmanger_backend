import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Set up Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.tasks.models import Task, TaskMember
from apps.comments.models import TaskComment
from apps.notifications.models import Notification
from apps.activity_logs.models import ActivityLog


def seed():
    print("Starting database seeding...")
    
    # 1. Clear existing data
    print("Clearing existing data...")
    ActivityLog.objects.all().delete()
    Notification.objects.all().delete()
    TaskComment.objects.all().delete()
    TaskMember.objects.all().delete()
    Task.objects.all().delete()
    User.objects.all().delete()
    
    # 2. Create Users
    print("Creating users...")
    admin = User.objects.create_superuser(
        email="admin@taskmanager.com",
        password="Admin@1234",
        first_name="Admin",
        last_name="System",
        profile_image="https://api.dicebear.com/7.x/bottts/svg?seed=Admin"
    )
    
    alice = User.objects.create_user(
        email="alice@taskmanager.com",
        password="User@1234",
        first_name="Alice",
        last_name="Johnson",
        is_verified=True,
        profile_image="https://api.dicebear.com/7.x/adventurer/svg?seed=Alice"
    )
    
    bob = User.objects.create_user(
        email="bob@taskmanager.com",
        password="User@1234",
        first_name="Bob",
        last_name="Smith",
        is_verified=True,
        profile_image="https://api.dicebear.com/7.x/adventurer/svg?seed=Bob"
    )
    
    charlie = User.objects.create_user(
        email="charlie@taskmanager.com",
        password="User@1234",
        first_name="Charlie",
        last_name="Brown",
        is_verified=True,
        profile_image="https://api.dicebear.com/7.x/adventurer/svg?seed=Charlie"
    )
    
    diana = User.objects.create_user(
        email="diana@taskmanager.com",
        password="User@1234",
        first_name="Diana",
        last_name="Prince",
        is_verified=True,
        profile_image="https://api.dicebear.com/7.x/adventurer/svg?seed=Diana"
    )
    
    print(f"Created users: {admin.email}, {alice.email}, {bob.email}, {charlie.email}, {diana.email}")

    # 3. Create Tasks
    print("Creating tasks...")
    now = timezone.now()
    
    t1 = Task.objects.create(
        created_by=admin,
        title="Setup Cloud Infrastructure",
        description="Configure AWS EC2 clusters, RDS PostgreSQL database replica, and initialize static S3 buckets for the production landing environment.",
        status="IN_PROGRESS",
        priority="HIGH",
        due_date=now + timedelta(days=3)
    )
    
    t2 = Task.objects.create(
        created_by=alice,
        title="Design UI Mockups",
        description="Deliver interactive Figma dashboards showing beautiful glassmorphism, responsive sidebar toggle, and high-fidelity task boards.",
        status="COMPLETED",
        priority="MEDIUM",
        due_date=now - timedelta(days=1)
    )
    
    t3 = Task.objects.create(
        created_by=admin,
        title="Integrate Google OAuth Authentication",
        description="Verify Google Client tokens on backend endpoints and create standard JWT sessions for logged-in social users.",
        status="PENDING",
        priority="HIGH",
        due_date=now + timedelta(days=5)
    )
    
    t4 = Task.objects.create(
        created_by=bob,
        title="Write API Documentation",
        description="Generate OpenAPI schema docs and compile robust Postman collections describing all user, task, and team invite APIs.",
        status="PENDING",
        priority="LOW",
        due_date=now + timedelta(days=10)
    )
    
    t5 = Task.objects.create(
        created_by=alice,
        title="Beta Testing Campaign",
        description="Coordinate internal developer testing, collect feedback on form validation alerts, and fix styling alignment issues.",
        status="CANCELLED",
        priority="MEDIUM",
        due_date=now + timedelta(days=14)
    )

    print("Created 5 sample tasks.")

    # 4. Create Task Members (Teammates assignments)
    print("Assigning teammates...")
    # Setup Cloud Infrastructure members
    TaskMember.objects.create(task=t1, user=bob, invited_email=bob.email, invitation_status='ACCEPTED', joined_at=now)
    TaskMember.objects.create(task=t1, user=charlie, invited_email=charlie.email, invitation_status='PENDING')
    
    # Design UI Mockups members
    TaskMember.objects.create(task=t2, user=diana, invited_email=diana.email, invitation_status='ACCEPTED', joined_at=now - timedelta(days=2))
    
    # Google OAuth members
    TaskMember.objects.create(task=t3, user=alice, invited_email=alice.email, invitation_status='ACCEPTED', joined_at=now)
    TaskMember.objects.create(task=t3, user=bob, invited_email=bob.email, invitation_status='PENDING')
    
    # API Documentation members
    TaskMember.objects.create(task=t4, user=charlie, invited_email=charlie.email, invitation_status='ACCEPTED', joined_at=now)
    
    print("Created teammate assignments.")

    # 5. Create Comments
    print("Adding task comments...")
    TaskComment.objects.create(
        task=t1,
        user=bob,
        comment="EC2 cluster is successfully provisioned. Starting RDS setup tonight."
    )
    TaskComment.objects.create(
        task=t1,
        user=admin,
        comment="Excellent progress Bob! Please ensure we enable encryption on the primary storage volume."
    )
    TaskComment.objects.create(
        task=t2,
        user=diana,
        comment="These figma screens look absolutely incredible! The glassmorphism card overlays feel extremely premium."
    )
    
    print("Created sample comments.")

    # 6. Create Notifications
    print("Creating sample notifications...")
    Notification.objects.create(
        user=bob,
        title="Assigned to Setup Cloud Infrastructure",
        message="You have been assigned to 'Setup Cloud Infrastructure' by admin@taskmanager.com.",
        type="TASK_ASSIGNED",
        is_read=False
    )
    Notification.objects.create(
        user=alice,
        title="Assigned to Integrate Google OAuth",
        message="You have been assigned to 'Integrate Google OAuth' by admin@taskmanager.com.",
        type="TASK_ASSIGNED",
        is_read=True
    )
    Notification.objects.create(
        user=admin,
        title="Invitation Accepted",
        message="bob@taskmanager.com accepted your invitation to Setup Cloud Infrastructure.",
        type="INVITATION_SENT",
        is_read=False
    )
    Notification.objects.create(
        user=charlie,
        title="Task Invitation: Setup Cloud Infrastructure",
        message="You have a pending invitation to collaborate on Setup Cloud Infrastructure.",
        type="TASK_ASSIGNED",
        is_read=False
    )

    print("Created sample notifications.")

    # 7. Create Activity Logs
    print("Logging activity...")
    ActivityLog.objects.create(user=admin, action="TASK_CREATED", details="Created task 'Setup Cloud Infrastructure'")
    ActivityLog.objects.create(user=alice, action="TASK_CREATED", details="Created task 'Design UI Mockups'")
    ActivityLog.objects.create(user=admin, action="TASK_CREATED", details="Created task 'Integrate Google OAuth'")
    ActivityLog.objects.create(user=bob, action="TASK_STATUS_CHANGED", details="Changed status of task 'Setup Cloud Infrastructure' to IN_PROGRESS")
    ActivityLog.objects.create(user=alice, action="TASK_STATUS_CHANGED", details="Changed status of task 'Design UI Mockups' to COMPLETED")

    print("Created sample activity logs.")
    print("Database seeding completed successfully!")


if __name__ == '__main__':
    seed()
