from django.db import models
from django.utils import timezone
import uuid
import hashlib

def hash_password(plain_text):
    if not plain_text:
        return ""
    return hashlib.sha256(plain_text.encode('utf-8')).hexdigest()

class UserAccount(models.Model):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('admin', 'Admin Officer'),
    )

    full_name = models.CharField(max_length=150, default='Citizen User')
    email = models.CharField(max_length=150, unique=True, db_index=True)
    phone = models.CharField(max_length=30, blank=True, default='')
    password_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    token = models.CharField(max_length=64, blank=True, default='')

    # OTP Verification
    otp_code = models.CharField(max_length=10, default='123456')
    otp_created_at = models.DateTimeField(default=timezone.now)

    # Demographic & Profile Details
    dob = models.CharField(max_length=30, blank=True, default='')
    gender = models.CharField(max_length=20, default='Male')
    state = models.CharField(max_length=100, default='')
    district = models.CharField(max_length=100, default='')
    address = models.TextField(blank=True, default='')

    # Occupation & Income
    occupation = models.CharField(max_length=50, default='General')
    income = models.IntegerField(default=0)
    education = models.CharField(max_length=50, default='General')
    category = models.CharField(max_length=30, default='General')

    # Disability & Preferences
    has_disability = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=100, blank=True, default='')
    disability_pct = models.IntegerField(default=0)
    email_alerts = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=True)
    share_profile = models.BooleanField(default=False)

    # Avatar
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password_hash = hash_password(raw_password)

    def check_password(self, raw_password):
        return self.password_hash == hash_password(raw_password)

    def generate_token(self):
        self.token = uuid.uuid4().hex
        self.save(update_fields=['token'])
        return self.token

    def calculate_completeness(self):
        fields = [
            self.full_name, self.dob, self.gender, self.state, self.district,
            self.address, self.email, self.phone, self.occupation,
            self.education, self.category
        ]
        filled = len([f for f in fields if f and str(f).strip()])
        return int(round((filled / len(fields)) * 100))

    def __str__(self):
        return f"{self.full_name} ({self.email}) [{self.role}]"


class Scheme(models.Model):
    scheme_code = models.CharField(max_length=50, unique=True, db_index=True, blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default='Social Welfare')
    ministry = models.CharField(max_length=255, default='Government of India')
    gov_level = models.CharField(max_length=50, default='Central Government')
    state_coverage = models.CharField(max_length=100, default='All India')
    status = models.CharField(max_length=50, default='Applications Open')
    
    objective = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    beneficiaries = models.TextField(blank=True, default='')

    benefits_summary = models.CharField(max_length=255, default='')
    benefits = models.JSONField(default=list, blank=True)
    eligibility = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)
    process = models.JSONField(default=list, blank=True)
    
    deadline = models.CharField(max_length=100, default='Ongoing')
    official_link = models.CharField(max_length=255, default='#')
    contact_info = models.JSONField(default=dict, blank=True)
    faqs = models.JSONField(default=list, blank=True)

    ai_score = models.IntegerField(default=95)
    ai_checklist = models.JSONField(default=list, blank=True)
    estimated_benefit = models.CharField(max_length=100, default='₹50,000')

    target_occupations = models.JSONField(default=list, blank=True)
    target_sectors = models.JSONField(default=list, blank=True)
    max_income = models.IntegerField(default=1200000)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.scheme_code:
            cat_prefix = (self.category[:3].upper()) if self.category else 'GEN'
            if len(cat_prefix) < 3:
                cat_prefix = cat_prefix.ljust(3, 'X')
            rand_code = uuid.uuid4().hex[:6].upper()
            self.scheme_code = f"SCH-{cat_prefix}-{rand_code}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.scheme_code or 'NO-CODE'} - {self.name} ({self.category})"


class UserDocument(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='documents')
    doc_key = models.CharField(max_length=50, default='Identity') # Identity, Income, Address, Marksheet, Other
    doc_type_name = models.CharField(max_length=150, default='Government Document')
    category = models.CharField(max_length=50, default='mandatory') # mandatory, academic, other
    file = models.FileField(upload_to='documents/', blank=True, null=True)
    file_name = models.CharField(max_length=255, default='document.pdf')
    file_size = models.CharField(max_length=50, default='1.2 MB')
    file_format = models.CharField(max_length=50, default='PDF Document')
    status = models.CharField(max_length=50, default='Verified') # Verified, Under Review, Pending, Rejected, Reupload
    admin_notes = models.TextField(blank=True, default='')

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.doc_key} ({self.file_name})"


class Application(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    application_id = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='applications')
    scheme = models.ForeignKey(Scheme, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    scheme_name = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='submitted')
    stage = models.IntegerField(default=0) # 0 to 4
    rejection_reason = models.TextField(blank=True, null=True)
    applicant_data = models.JSONField(default=dict, blank=True)

    submitted_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.application_id} - {self.scheme_name} [{self.status}]"


class SchemeBookmark(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='bookmarks')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'scheme')

    def __str__(self):
        return f"{self.user.email} -> {self.scheme.name}"


class SchemeFeedback(models.Model):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(default=5)
    feedback_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback ({self.rating}★) for {self.scheme.name}"


class SchemeReport(models.Model):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    issues = models.JSONField(default=list)
    details = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.scheme.name} - Resolved: {self.resolved}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    status = models.CharField(max_length=30, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact: {self.name} - {self.subject}"


class SchemeUpdate(models.Model):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='updates')
    ministry_or_node = models.CharField(max_length=150, default='State Welfare Department')
    change_summary = models.TextField()
    status = models.CharField(max_length=30, default='pending') # pending, approved, rejected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for {self.scheme.name} - {self.status}"
