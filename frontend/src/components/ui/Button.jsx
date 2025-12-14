import { clsx } from 'clsx';

export default function Button({
    children,
    variant = 'primary',
    className = '',
    disabled = false,
    loading = false,
    ...props
}) {
    return (
        <button
            className={clsx(
                variant === 'primary' ? 'btn-primary' : 'btn-secondary',
                disabled && 'opacity-50 cursor-not-allowed',
                className
            )}
            disabled={disabled || loading}
            {...props}
        >
            {loading ? (
                <span className="flex items-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                        />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                    </svg>
                    جاري التحميل...
                </span>
            ) : children}
        </button>
    );
}
