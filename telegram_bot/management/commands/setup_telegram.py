# telegram_bot/management/commands/setup_telegram.py

import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup Telegram bot webhook and verify configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--set-webhook',
            action='store_true',
            help='Set webhook URL for the bot',
        )
        parser.add_argument(
            '--delete-webhook',
            action='store_true',
            help='Delete current webhook',
        )
        parser.add_argument(
            '--get-webhook-info',
            action='store_true',
            help='Get current webhook information',
        )
        parser.add_argument(
            '--get-me',
            action='store_true',
            help='Get bot information',
        )
        parser.add_argument(
            '--test-bot',
            action='store_true',
            help='Run comprehensive bot test',
        )

    def handle(self, *args, **options):
        # Check if bot token is configured
        if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            raise CommandError(
                'TELEGRAM_BOT_TOKEN not configured in settings. '
                'Please set it in your .env file or environment variables.'
            )

        if options['set_webhook']:
            self.set_webhook()
        elif options['delete_webhook']:
            self.delete_webhook()
        elif options['get_webhook_info']:
            self.get_webhook_info()
        elif options['get_me']:
            self.get_bot_info()
        elif options['test_bot']:
            self.test_bot()
        else:
            self.stdout.write(
                self.style.WARNING('No action specified. Use --help to see available options.')
            )

    def get_api_url(self, method):
        """Get full API URL for a method"""
        return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"

    def make_request(self, method, data=None):
        """Make API request to Telegram"""
        url = self.get_api_url(method)
        try:
            if data:
                response = requests.post(url, data=data)
            else:
                response = requests.get(url)
            
            return response.json()
        except requests.RequestException as e:
            raise CommandError(f'API request failed: {e}')

    def set_webhook(self):
        """Set webhook URL"""
        webhook_url = f"{settings.TELEGRAM_WEBHOOK_BASE_URL}/telegram/webhook/"
        
        self.stdout.write(f'Setting webhook to: {webhook_url}')
        
        data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query']
        }
        
        result = self.make_request('setWebhook', data)
        
        if result.get('ok'):
            self.stdout.write(
                self.style.SUCCESS(f'✅ Webhook successfully set to: {webhook_url}')
            )
        else:
            error_msg = result.get('description', 'Unknown error')
            raise CommandError(f'❌ Failed to set webhook: {error_msg}')

    def delete_webhook(self):
        """Delete current webhook"""
        self.stdout.write('Deleting webhook...')
        
        result = self.make_request('deleteWebhook')
        
        if result.get('ok'):
            self.stdout.write(
                self.style.SUCCESS('✅ Webhook successfully deleted')
            )
        else:
            error_msg = result.get('description', 'Unknown error')
            raise CommandError(f'❌ Failed to delete webhook: {error_msg}')

    def get_webhook_info(self):
        """Get current webhook information"""
        self.stdout.write('Getting webhook info...')
        
        result = self.make_request('getWebhookInfo')
        
        if result.get('ok'):
            webhook_info = result.get('result', {})
            
            self.stdout.write('\n📋 Webhook Information:')
            self.stdout.write(f"  URL: {webhook_info.get('url', 'Not set')}")
            self.stdout.write(f"  Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
            self.stdout.write(f"  Pending update count: {webhook_info.get('pending_update_count', 0)}")
            self.stdout.write(f"  Last error date: {webhook_info.get('last_error_date', 'None')}")
            self.stdout.write(f"  Last error message: {webhook_info.get('last_error_message', 'None')}")
            self.stdout.write(f"  Max connections: {webhook_info.get('max_connections', 40)}")
            
            allowed_updates = webhook_info.get('allowed_updates', [])
            self.stdout.write(f"  Allowed updates: {', '.join(allowed_updates) if allowed_updates else 'All'}")
            
        else:
            error_msg = result.get('description', 'Unknown error')
            raise CommandError(f'❌ Failed to get webhook info: {error_msg}')

    def get_bot_info(self):
        """Get bot information"""
        self.stdout.write('Getting bot info...')
        
        result = self.make_request('getMe')
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            
            self.stdout.write('\n🤖 Bot Information:')
            self.stdout.write(f"  ID: {bot_info.get('id')}")
            self.stdout.write(f"  Username: @{bot_info.get('username')}")
            self.stdout.write(f"  First name: {bot_info.get('first_name')}")
            self.stdout.write(f"  Is bot: {bot_info.get('is_bot')}")
            self.stdout.write(f"  Can join groups: {bot_info.get('can_join_groups')}")
            self.stdout.write(f"  Can read all group messages: {bot_info.get('can_read_all_group_messages')}")
            self.stdout.write(f"  Supports inline queries: {bot_info.get('supports_inline_queries')}")
            
        else:
            error_msg = result.get('description', 'Unknown error')
            raise CommandError(f'❌ Failed to get bot info: {error_msg}')

    def test_bot(self):
        """Run comprehensive bot test"""
        self.stdout.write(self.style.WARNING('🧪 Running comprehensive bot test...\n'))
        
        # Test 1: Bot info
        self.stdout.write('1️⃣ Testing bot authentication...')
        try:
            self.get_bot_info()
            self.stdout.write(self.style.SUCCESS('   ✅ Bot authentication: PASSED\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Bot authentication: FAILED - {e}\n'))
            return

        # Test 2: Webhook info
        self.stdout.write('2️⃣ Testing webhook configuration...')
        try:
            self.get_webhook_info()
            self.stdout.write(self.style.SUCCESS('   ✅ Webhook configuration: PASSED\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Webhook configuration: FAILED - {e}\n'))

        # Test 3: Django settings
        self.stdout.write('3️⃣ Testing Django settings...')
        
        required_settings = [
            ('TELEGRAM_BOT_TOKEN', settings.TELEGRAM_BOT_TOKEN),
            ('TELEGRAM_WEBHOOK_BASE_URL', settings.TELEGRAM_WEBHOOK_BASE_URL),
        ]
        
        all_settings_ok = True
        for setting_name, setting_value in required_settings:
            if not setting_value or 'your' in setting_value.lower():
                self.stdout.write(self.style.ERROR(f'   ❌ {setting_name}: NOT CONFIGURED'))
                all_settings_ok = False
            else:
                self.stdout.write(self.style.SUCCESS(f'   ✅ {setting_name}: OK'))
        
        if all_settings_ok:
            self.stdout.write(self.style.SUCCESS('   ✅ Django settings: PASSED\n'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Django settings: FAILED\n'))

        # Test 4: URL accessibility (basic check)
        self.stdout.write('4️⃣ Testing webhook URL accessibility...')
        webhook_url = f"{settings.TELEGRAM_WEBHOOK_BASE_URL}/telegram/webhook/"
        
        if 'localhost' in webhook_url or '127.0.0.1' in webhook_url:
            self.stdout.write(self.style.WARNING(
                '   ⚠️  Webhook URL uses localhost. This won\'t work with Telegram. '
                'Use ngrok or deploy to a public server.\n'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Webhook URL format: OK ({webhook_url})\n'))

        # Summary
        self.stdout.write(self.style.SUCCESS('🎉 Bot test completed!'))
        self.stdout.write('\n📝 Next steps:')
        self.stdout.write('   1. If using localhost, set up ngrok: ngrok http 8000')
        self.stdout.write('   2. Update TELEGRAM_WEBHOOK_BASE_URL with your ngrok URL')
        self.stdout.write('   3. Run: python manage.py setup_telegram --set-webhook')
        self.stdout.write('   4. Test your bot by sending /start to @' + 
                         getattr(settings, 'TELEGRAM_BOT_USERNAME', 'your_bot'))
        self.stdout.write('   5. Check Django logs for incoming webhooks')