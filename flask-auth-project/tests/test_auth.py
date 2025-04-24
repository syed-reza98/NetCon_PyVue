from flask import Flask, jsonify
from flask_testing import TestCase
from src.app import app
from src.models.user import User
from src.services.auth_service import AuthService

class TestAuth(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        self.auth_service = AuthService()
        self.user_data = {
            'username': 'testuser',
            'password': 'testpassword',
            'role': 'user'
        }
        self.auth_service.register_user(self.user_data)

    def tearDown(self):
        User.query.delete()

    def test_user_registration(self):
        response = self.auth_service.register_user({
            'username': 'newuser',
            'password': 'newpassword',
            'role': 'user'
        })
        self.assertTrue(response)

    def test_user_login(self):
        response = self.auth_service.login_user(self.user_data['username'], self.user_data['password'])
        self.assertIsNotNone(response)

    def test_login_with_invalid_credentials(self):
        response = self.auth_service.login_user('invaliduser', 'wrongpassword')
        self.assertIsNone(response)

    def test_user_role_assignment(self):
        user = User.query.filter_by(username=self.user_data['username']).first()
        user.assign_role('admin')
        self.assertIn('admin', user.roles)

    def test_user_permission_check(self):
        user = User.query.filter_by(username=self.user_data['username']).first()
        user.assign_role('admin')
        self.assertTrue(user.has_permission('admin_permission'))