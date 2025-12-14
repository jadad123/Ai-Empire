import { useTranslation } from 'react-i18next';
import { Settings as SettingsIcon, Globe, Key, Image, Database } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

export default function Settings() {
    const { t, i18n } = useTranslation();

    const toggleLanguage = () => {
        i18n.changeLanguage(i18n.language === 'ar' ? 'en' : 'ar');
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold">{t('nav.settings')}</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Language */}
                <Card>
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                            <Globe className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="font-semibold">اللغة</h3>
                            <p className="text-sm text-gray-400">تغيير لغة الواجهة</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button variant={i18n.language === 'ar' ? 'primary' : 'secondary'} onClick={() => i18n.changeLanguage('ar')}>العربية</Button>
                        <Button variant={i18n.language === 'en' ? 'primary' : 'secondary'} onClick={() => i18n.changeLanguage('en')}>English</Button>
                    </div>
                </Card>

                {/* API Keys */}
                <Card>
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                            <Key className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="font-semibold">مفاتيح API</h3>
                            <p className="text-sm text-gray-400">Gemini, Groq, Pexels</p>
                        </div>
                    </div>
                    <p className="text-sm text-gray-500 mb-2">يتم تكوين المفاتيح في ملف .env</p>
                    <code className="text-xs text-gray-400 block bg-black/30 p-2 rounded">GEMINI_API_KEY=...</code>
                </Card>

                {/* Image Settings */}
                <Card>
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
                            <Image className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="font-semibold">إعدادات الصور</h3>
                            <p className="text-sm text-gray-400">Bing, Flux, العلامة المائية</p>
                        </div>
                    </div>
                    <p className="text-sm text-gray-500">يتم تكوين كوكي Bing لكل موقع من صفحة المواقع</p>
                </Card>

                {/* Database */}
                <Card>
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                            <Database className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="font-semibold">قاعدة البيانات</h3>
                            <p className="text-sm text-gray-400">PostgreSQL + ChromaDB</p>
                        </div>
                    </div>
                    <p className="text-sm text-gray-500">تم التكوين عبر Docker Compose</p>
                </Card>
            </div>

            {/* Info */}
            <Card>
                <h3 className="font-semibold mb-4">معلومات النظام</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 glass-card-light rounded-lg">
                        <p className="text-lg font-bold">1.0.0</p>
                        <p className="text-xs text-gray-400">الإصدار</p>
                    </div>
                    <div className="text-center p-4 glass-card-light rounded-lg">
                        <p className="text-lg font-bold">Python 3.11</p>
                        <p className="text-xs text-gray-400">Backend</p>
                    </div>
                    <div className="text-center p-4 glass-card-light rounded-lg">
                        <p className="text-lg font-bold">React 18</p>
                        <p className="text-xs text-gray-400">Frontend</p>
                    </div>
                    <div className="text-center p-4 glass-card-light rounded-lg">
                        <p className="text-lg font-bold">Docker</p>
                        <p className="text-xs text-gray-400">Infrastructure</p>
                    </div>
                </div>
            </Card>
        </div>
    );
}
