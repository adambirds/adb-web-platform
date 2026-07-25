from django.db import models


class Server(models.Model):
    """Physical or virtual server"""

    PROVIDER_CHOICES = [
        ("do", "DigitalOcean"),
        ("aws", "AWS"),
        ("linode", "Linode"),
        ("vultr", "Vultr"),
        ("google_cloud", "Google Cloud"),
        ("azure", "Azure"),
        ("on_premise", "On-Premise"),
        ("other", "Other"),
    ]

    OS_CHOICES = [
        ("ubuntu_20", "Ubuntu 20.04"),
        ("ubuntu_22", "Ubuntu 22.04"),
        ("ubuntu_24", "Ubuntu 24.04"),
        ("debian_11", "Debian 11"),
        ("debian_12", "Debian 12"),
        ("centos_7", "CentOS 7"),
        ("centos_8", "CentOS 8"),
        ("other", "Other"),
    ]

    ROLE_CHOICES = [
        ("web", "Web Server"),
        ("database", "Database"),
        ("management", "Management"),
        ("ci", "CI/CD"),
        ("backup", "Backup"),
        ("cache", "Cache"),
        ("other", "Other"),
    ]

    # Basic info
    hostname = models.CharField(max_length=200)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="web")

    # Network
    public_ip = models.GenericIPAddressField(blank=True, null=True)
    private_ip = models.GenericIPAddressField(blank=True, null=True)

    # Provider & location
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    region = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=50, choices=OS_CHOICES)

    # Hardware
    cpu = models.CharField(max_length=100, blank=True)
    ram_gb = models.IntegerField(blank=True, null=True)
    disk_gb = models.IntegerField(blank=True, null=True)

    # Virtualization
    virtualization_type = models.CharField(
        max_length=50,
        choices=[
            ("bare_metal", "Bare Metal"),
            ("vm", "Virtual Machine"),
            ("container_host", "Container Host"),
        ],
        default="vm",
    )

    # Metadata
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return self.hostname


class Database(models.Model):
    """Database instance"""

    TYPE_CHOICES = [
        ("mysql", "MySQL"),
        ("postgres", "PostgreSQL"),
        ("mongodb", "MongoDB"),
        ("redis", "Redis"),
        ("mariadb", "MariaDB"),
        ("other", "Other"),
    ]

    PROVIDER_CHOICES = [
        ("self_hosted", "Self-Hosted"),
        ("do", "DigitalOcean"),
        ("aws_rds", "AWS RDS"),
        ("aws_dynamodb", "AWS DynamoDB"),
        ("google_cloud", "Google Cloud"),
        ("azure", "Azure"),
        ("heroku", "Heroku"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    db_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)

    # For self-hosted
    server = models.ForeignKey(Server, on_delete=models.SET_NULL, null=True, blank=True)

    version = models.CharField(max_length=50, blank=True)

    # Backup info
    backup_strategy = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Databases"

    def __str__(self):
        return self.name


class Website(models.Model):
    """Website or web application"""

    ENVIRONMENT_CHOICES = [
        ("production", "Production"),
        ("staging", "Staging"),
        ("development", "Development"),
        ("testing", "Testing"),
    ]

    name = models.CharField(max_length=200)
    primary_url = models.URLField()
    environment_type = models.CharField(max_length=50, choices=ENVIRONMENT_CHOICES, default="production")

    # Hosting
    servers = models.ManyToManyField(Server, related_name="websites")
    database = models.ForeignKey(Database, on_delete=models.SET_NULL, null=True, blank=True)

    # Admin/Access
    admin_url = models.URLField(blank=True)

    # GitHub
    github_repository = models.URLField(blank=True)

    # CDN & Cache
    has_cdn = models.BooleanField(default=False)
    cdn_provider = models.CharField(max_length=100, blank=True)
    cache_layer = models.CharField(max_length=100, blank=True, help_text="e.g., Varnish, Redis")

    # Aliases/Redirects
    aliases = models.TextField(blank=True, help_text="Comma-separated list")

    # Staging info
    staging_site = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class WebsiteTechStack(models.Model):
    """Technology used in a website"""

    CATEGORY_CHOICES = [
        ("frontend", "Frontend"),
        ("backend", "Backend"),
        ("database", "Database"),
        ("cms", "CMS"),
        ("other", "Other"),
    ]

    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name="tech_stack")
    technology = models.CharField(max_length=200, help_text="e.g., Next.js, Django, PostgreSQL")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    version = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("website", "technology")

    def __str__(self):
        return f"{self.website} - {self.technology}"


class Domain(models.Model):
    """Domain registration"""

    REGISTRAR_CHOICES = [
        ("godaddy", "GoDaddy"),
        ("namecheap", "Namecheap"),
        ("route53", "Route 53"),
        ("cloudflare", "Cloudflare"),
        ("google_domains", "Google Domains"),
        ("other", "Other"),
    ]

    domain_name = models.CharField(max_length=200, unique=True)
    registrar = models.CharField(max_length=50, choices=REGISTRAR_CHOICES)
    expiry_date = models.DateField()
    auto_renew = models.BooleanField(default=True)

    nameservers = models.TextField(blank=True, help_text="Comma-separated list")

    websites = models.ManyToManyField(Website, related_name="domains", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain_name"]

    def __str__(self):
        return self.domain_name


class SSLCertificate(models.Model):
    """SSL certificate tracking"""

    PROVIDER_CHOICES = [
        ("letsencrypt", "Let's Encrypt"),
        ("cloudflare", "Cloudflare"),
        ("comodo", "Comodo"),
        ("sectigo", "Sectigo"),
        ("other", "Other"),
    ]

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="ssl_certificates")
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    cert_type = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain"]

    def __str__(self):
        return f"{self.domain} SSL"


class Licence(models.Model):
    """Software or plugin license"""

    TYPE_CHOICES = [
        ("subscription", "Subscription"),
        ("perpetual", "Perpetual"),
        ("trial", "Trial"),
    ]

    name = models.CharField(max_length=200)
    licence_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    vendor = models.CharField(max_length=200)

    renewal_date = models.DateField()
    renewal_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    auto_renew = models.BooleanField(default=True)

    portal_url = models.URLField(blank=True)
    licence_key = models.CharField(max_length=500, blank=True)

    websites = models.ManyToManyField(Website, related_name="licences", blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-renewal_date"]

    def __str__(self):
        return self.name


class Application(models.Model):
    """Logical application (can span multiple components)"""

    TYPE_CHOICES = [
        ("web_app", "Web Application"),
        ("saas", "SaaS"),
        ("bot", "Bot"),
        ("mobile", "Mobile App"),
        ("hybrid", "Hybrid"),
        ("api", "API"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("maintenance", "Maintenance"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    app_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="active")

    # Components
    websites = models.ManyToManyField(Website, related_name="applications", blank=True)
    servers = models.ManyToManyField(Server, related_name="applications", blank=True)
    databases = models.ManyToManyField(Database, related_name="applications", blank=True)
    domains = models.ManyToManyField(Domain, related_name="applications", blank=True)
    licences = models.ManyToManyField(Licence, related_name="applications", blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class MobileApp(models.Model):
    """Mobile application"""

    PLATFORM_CHOICES = [
        ("ios", "iOS"),
        ("android", "Android"),
        ("both", "Both (Cross-platform)"),
    ]

    FRAMEWORK_CHOICES = [
        ("swift", "Swift"),
        ("kotlin", "Kotlin"),
        ("react_native", "React Native"),
        ("flutter", "Flutter"),
        ("other", "Other"),
    ]

    RELEASE_STATUS_CHOICES = [
        ("development", "Development"),
        ("testing", "Testing"),
        ("live", "Live"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    framework = models.CharField(max_length=50, choices=FRAMEWORK_CHOICES)

    bundle_id = models.CharField(max_length=200, blank=True, help_text="Android package name or iOS bundle ID")
    current_version = models.CharField(max_length=50, blank=True)
    release_status = models.CharField(max_length=50, choices=RELEASE_STATUS_CHOICES, default="development")

    # Store links
    app_store_link = models.URLField(blank=True)
    play_store_link = models.URLField(blank=True)

    # Backend
    backend_api = models.URLField(blank=True)
    github_repository = models.URLField(blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class API(models.Model):
    """API endpoint or service"""

    TYPE_CHOICES = [
        ("rest", "REST"),
        ("graphql", "GraphQL"),
        ("webhook", "Webhook"),
        ("rpc", "RPC"),
        ("internal", "Internal"),
    ]

    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private_key", "Private (API Key)"),
        ("private_session", "Private (Session)"),
    ]

    AUTH_CHOICES = [
        ("none", "None"),
        ("api_key", "API Key"),
        ("oauth", "OAuth"),
        ("jwt", "JWT"),
        ("session", "Session"),
    ]

    name = models.CharField(max_length=200)
    api_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)

    base_url = models.URLField()
    visibility = models.CharField(max_length=50, choices=VISIBILITY_CHOICES, default="private_session")
    authentication = models.CharField(max_length=50, choices=AUTH_CHOICES, default="session")

    # Versioning
    versioning_strategy = models.CharField(max_length=100, blank=True)

    # Rate limiting
    rate_limiting = models.TextField(blank=True)

    # Documentation
    documentation_url = models.URLField(blank=True)
    github_repository = models.URLField(blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Bot(models.Model):
    """Chat bot or automation"""

    PLATFORM_CHOICES = [
        ("twitch", "Twitch"),
        ("discord", "Discord"),
        ("slack", "Slack"),
        ("custom", "Custom"),
    ]

    TYPE_CHOICES = [
        ("chat", "Chat Bot"),
        ("moderation", "Moderation"),
        ("automation", "Automation"),
        ("integration", "Integration"),
    ]

    RUNTIME_CHOICES = [
        ("python", "Python"),
        ("nodejs", "Node.js"),
        ("go", "Go"),
        ("rust", "Rust"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    bot_type = models.CharField(max_length=50, choices=TYPE_CHOICES)

    runtime = models.CharField(max_length=50, choices=RUNTIME_CHOICES)
    hosting_location = models.CharField(max_length=200, blank=True)

    permissions = models.TextField(blank=True, help_text="List of permissions/scopes")
    github_repository = models.URLField(blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class EmailSystem(models.Model):
    """Email system configuration"""

    PROVIDER_CHOICES = [
        ("exchange", "Microsoft Exchange"),
        ("microsoft_365", "Microsoft 365"),
        ("google_workspace", "Google Workspace"),
        ("self_hosted", "Self-Hosted"),
    ]

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    admin_portal_url = models.URLField(blank=True)

    # Domains & setup
    domains = models.TextField(blank=True, help_text="Comma-separated list")
    spf_status = models.CharField(max_length=50, blank=True)
    dkim_status = models.CharField(max_length=50, blank=True)
    dmarc_status = models.CharField(max_length=50, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} Email System"
