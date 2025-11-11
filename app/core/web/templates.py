from fastapi.templating import Jinja2Templates
from app.core.security.csrf import generate_csrf_token


class CustomJinja2Templates(Jinja2Templates):
    """
    Кастомный Jinja2Templates с автоматическим добавлением current_user и csrf_token
    """
    def TemplateResponse(self, name, context=None, **kwargs):
        if context is None:
            context = {}

        request = context.get("request")
        if request:
            # Автоматически добавляем current_user из request.state
            if hasattr(request.state, "current_user"):
                context["current_user"] = request.state.current_user

            # Автоматически генерируем и добавляем csrf_token из session
            csrf_token = generate_csrf_token(request)
            context["csrf_token"] = csrf_token

        return super().TemplateResponse(name, context, **kwargs)


templates = CustomJinja2Templates(directory="app/templates")
