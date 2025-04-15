from django.db import models
from django.contrib.auth.models import User

class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    natural_language = models.TextField()
    sql_query = models.TextField()
    result = models.JSONField(null=True, blank=True)  # result field stores JSON data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Queries'

    def __str__(self):
        return f"{self.natural_language[:50]}"


class QueryFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    help_full = models.BooleanField(default=False)                        # Default: False
    nlp_given = models.TextField(default="")                             # Default: empty string
    query_sql = models.TextField(default="")                             # Default: empty string
    query_user = models.ForeignKey(User, on_delete=models.CASCADE)       # Must be provided explicitly
    rating = models.IntegerField(choices=RATING_CHOICES, default=3)      # Default: 3 (midpoint)
    comments = models.TextField(blank=True, null=True, default="")       # Default: empty string
    created_at = models.DateTimeField(auto_now_add=True)                 # Auto-set at creation

    def __str__(self):
        return f"Feedback from {self.query_user.username} | Rating: {self.rating}"
