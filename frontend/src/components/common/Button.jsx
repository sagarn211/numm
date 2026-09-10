import { Loader2 } from 'lucide-react';

export const Button = ({
  children,
  variant = 'primary', // primary | secondary | danger | ghost | success
  size = 'md', // sm | md | lg
  icon: Icon,
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-[#8B634E] hover:bg-[#6C4738] text-white focus:ring-[#8B634E] shadow-[0_4px_12px_rgba(107,74,56,0.22)] hover:shadow-[0_6px_16px_rgba(107,74,56,0.28)] hover:-translate-y-0.5',
    secondary: 'bg-white hover:bg-[#f6efe8] text-[#4a4039] border border-[#dcc9b8] focus:ring-[#ab7f62] shadow-[0_2px_8px_rgba(60,47,39,0.05)]',
    danger: 'bg-[#b75d50] hover:bg-[#9e4f46] text-white focus:ring-[#b75d50] shadow-[0_4px_12px_rgba(183,93,80,0.2)] hover:shadow-[0_6px_16px_rgba(183,93,80,0.28)] hover:-translate-y-0.5',
    ghost: 'bg-transparent hover:bg-[#f3e8dd] text-[#5b4d44] hover:text-[#2f261f] border border-transparent shadow-none',
    success: 'bg-[#6b8d63] hover:bg-[#577154] text-white focus:ring-[#6b8d63] shadow-[0_4px_12px_rgba(107,141,99,0.2)] hover:shadow-[0_6px_16px_rgba(107,141,99,0.28)] hover:-translate-y-0.5',
  };

  const sizes = {
    sm: 'px-3.5 py-1.5 text-[13px] gap-1.5',
    md: 'px-5 py-2.5 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : Icon ? (
        <Icon className="w-4 h-4 text-current" />
      ) : null}
      <span>{children}</span>
    </button>
  );
};
