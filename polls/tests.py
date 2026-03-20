import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question


def create_question(question_text, days, description=""):
    """
    Crea una pregunta con el texto dado y publicada en `days` días desde ahora.
    Días negativos = pasado; positivos = futuro.
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(
        question_text=question_text,
        description=description,
        pub_date=time,
    )


# ── Tests del modelo ────────────────────────────────────────────

class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """was_published_recently() devuelve False para preguntas futuras."""
        future_question = create_question("Pregunta futura", days=30)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """was_published_recently() devuelve False para preguntas de más de 1 día."""
        old_question = create_question("Pregunta vieja", days=-2)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """was_published_recently() devuelve True para preguntas de menos de 1 día."""
        recent_question = create_question("Pregunta reciente", days=0)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_question_str(self):
        """__str__ devuelve el texto de la pregunta."""
        q = create_question("¿Cuál es tu color favorito?", days=0)
        self.assertEqual(str(q), "¿Cuál es tu color favorito?")

    def test_description_optional(self):
        """El campo descripción puede estar vacío."""
        q = create_question("Pregunta sin descripción", days=0)
        self.assertEqual(q.description, "")

    def test_description_saved_correctly(self):
        """El campo descripción se guarda correctamente."""
        q = create_question("Pregunta con descripción", days=0, description="Esta es la descripción.")
        q.refresh_from_db()
        self.assertEqual(q.description, "Esta es la descripción.")


# ── Tests de la vista Index ──────────────────────────────────────

class QuestionIndexViewTests(TestCase):

    def test_no_questions(self):
        """Sin preguntas muestra el mensaje de vacío."""
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay encuestas disponibles")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """Preguntas del pasado aparecen en el índice."""
        question = create_question("Pregunta pasada", days=-1)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_future_question(self):
        """Preguntas futuras NO aparecen en el índice."""
        create_question("Pregunta futura", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No hay encuestas disponibles")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_and_past_question(self):
        """Con preguntas pasadas y futuras, solo aparece la pasada."""
        question = create_question("Pregunta pasada", days=-1)
        create_question("Pregunta futura", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_two_past_questions(self):
        """Se muestran múltiples preguntas pasadas."""
        q1 = create_question("Pregunta 1", days=-2)
        q2 = create_question("Pregunta 2", days=-1)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [q2, q1])

    def test_description_shown_in_index(self):
        """Si la pregunta tiene descripción, se muestra en el índice."""
        create_question("Pregunta con desc", days=-1, description="Descripción visible")
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "Descripción visible")


# ── Tests de la vista Detail ─────────────────────────────────────

class QuestionDetailViewTests(TestCase):

    def test_future_question(self):
        """La vista detail devuelve 404 para preguntas futuras."""
        future_question = create_question("Futura", days=5)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """La vista detail muestra la pregunta si es del pasado."""
        past_question = create_question("Pasada", days=-1)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_description_shown_in_detail(self):
        """La descripción se muestra en la vista de detalle."""
        q = create_question("Pregunta", days=-1, description="Descripción detallada")
        url = reverse("polls:detail", args=(q.id,))
        response = self.client.get(url)
        self.assertContains(response, "Descripción detallada")
