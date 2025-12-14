import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout({ children }) {
    return (
        <div className="min-h-screen">
            <Sidebar />
            <main className="mr-64 rtl:mr-64 ltr:ml-64 p-6">
                <Header />
                <div className="animate-fade-in">
                    {children}
                </div>
            </main>
        </div>
    );
}
