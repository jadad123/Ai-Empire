import { clsx } from 'clsx';

export default function Card({ children, className = '', glow = false }) {
    return (
        <div className={clsx(
            'glass-card p-6',
            glow && 'glow',
            className
        )}>
            {children}
        </div>
    );
}
