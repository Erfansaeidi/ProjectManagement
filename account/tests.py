import shutil
import tempfile
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Profile, WorkGroup

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def generate_test_image(name: str = 'avatar.png', fmt: str = 'PNG', size=(64, 64)) -> SimpleUploadedFile:
    buffer = BytesIO()
    image = Image.new('RGB', size, color=(40, 120, 200))
    image.save(buffer, format=fmt)
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type=f'image/{fmt.lower()}')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AccountRoleGroupAndProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user_a = User.objects.create_user(username='alice', email='alice@example.com', password='StrongPassword123!')
        self.user_b = User.objects.create_user(username='bob', email='bob@example.com', password='StrongPassword123!')
        self.user_c = User.objects.create_user(username='charlie', email='charlie@example.com', password='StrongPassword123!')

    def test_new_user_receives_none_role_and_profile(self):
        self.assertEqual(self.user_a.profile.role, Profile.Role.NONE)
        self.assertIsNone(self.user_a.profile.group)

    def test_role_cannot_be_escalated_via_profile_edit_post(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            reverse('profile_edit'),
            data={
                'first_name': 'Alice',
                'last_name': 'Smith',
                'email': 'alice@example.com',
                'bio': 'Updated bio',
                'role': Profile.Role.ADMIN,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user_a.profile.refresh_from_db()
        self.assertEqual(self.user_a.profile.role, Profile.Role.NONE)
        self.assertEqual(self.user_a.profile.bio, 'Updated bio')

    def test_profile_picture_upload_replace_and_remove(self):
        self.client.force_login(self.user_a)
        first_img = generate_test_image('first.png')
        self.client.post(
            reverse('profile_edit'),
            data={
                'first_name': 'Alice',
                'last_name': '',
                'email': 'alice@example.com',
                'bio': '',
                'profile_picture': first_img,
            },
        )
        self.user_a.profile.refresh_from_db()
        first_name = self.user_a.profile.profile_picture.name
        self.assertTrue(first_name.startswith('profile_pictures/'))
        self.assertNotIn('first.png', first_name)

        self.client.post(reverse('profile_picture_delete'))
        self.user_a.profile.refresh_from_db()
        self.assertFalse(bool(self.user_a.profile.profile_picture))

    def test_invalid_profile_picture_rejected(self):
        self.client.force_login(self.user_a)
        fake_img = SimpleUploadedFile('malware.png', b'not-an-image-content', content_type='image/png')
        response = self.client.post(
            reverse('profile_edit'),
            data={
                'first_name': 'Alice',
                'last_name': '',
                'email': 'alice@example.com',
                'bio': '',
                'profile_picture': fake_img,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user_a.profile.refresh_from_db()
        self.assertFalse(bool(self.user_a.profile.profile_picture))

    def test_group_creation_membership_and_isolation(self):
        self.client.force_login(self.user_a)
        self.client.post(reverse('group_create'), data={'name': 'Alpha Team', 'description': 'Core'})
        self.user_a.profile.refresh_from_db()
        self.assertEqual(self.user_a.profile.role, Profile.Role.MANAGER)

        self.client.post(reverse('group_add_member'), data={'username': 'bob'})
        self.user_b.profile.refresh_from_db()
        self.assertEqual(self.user_b.profile.role, Profile.Role.MEMBER)

        # Same group member can view teammate profile
        self.client.force_login(self.user_b)
        allowed_resp = self.client.get(reverse('user_profile_detail', args=[self.user_a.id]))
        self.assertEqual(allowed_resp.status_code, 200)

        # User outside group cannot view group or teammate profile (IDOR check)
        self.client.force_login(self.user_c)
        forbidden_profile = self.client.get(reverse('user_profile_detail', args=[self.user_a.id]))
        self.assertEqual(forbidden_profile.status_code, 403)
        forbidden_group = self.client.get(reverse('group_detail'))
        self.assertEqual(forbidden_group.status_code, 403)