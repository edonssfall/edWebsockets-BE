from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View

User = get_user_model()


class UserSearchAPIView(View):
    def post(self, request):
        users = User.objects.filter(
            username__icontains=request.data['search']
        )

        return JsonResponse({'results': users})