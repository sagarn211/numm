import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, ShieldCheck, Lock, Mail, ArrowRight, Sparkles, User as UserIcon } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { authApi } from '../services/authApi';
import { Button } from '../components/common/Button';

export const Login = () => {
  const navigate = useNavigate();
  const { login, loading } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [cpses, setCpses] = useState([]);
  const [cpseId, setCpseId] = useState('');
  const [email, setEmail] = useState('officer@numm.gov.in');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [regSuccess, setRegSuccess] = useState('');
  const [error, setError] = useState(() => {
    const message = sessionStorage.getItem('numm_session_message') || '';
    sessionStorage.removeItem('numm_session_message');
    return message;
  });

  useEffect(() => {
    authApi.getRegistrationCpses().then(response => setCpses(response.data || [])).catch(() => setCpses([]));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (isRegister) {
      try {
        const response = await authApi.register({
          name,
          email,
          password,
          role: 'REQUESTING_OFFICER',
          cpse_id: Number(cpseId),
        });
        setRegSuccess(response.data?.message || 'Registration submitted. Wait for administrator approval before signing in.');
        setPassword('');
        setIsRegister(false);
      } catch (err) {
        setError(err?.response?.data?.detail || err.message || 'Registration failed');
      }
    } else {
      try { await login(email, password); navigate('/dashboard'); }
      catch (err) { setError(err?.response?.data?.detail || err.message || 'Login failed'); }
    }
  };

  return (
    <div className="min-h-screen bg-[#F3EDE5] flex items-center justify-center p-4 md:p-8 relative overflow-hidden font-sans">
      {/* Background Decorative Grids */}
      <div className="absolute inset-0 bg-[radial-gradient(#d7cab8_1px,transparent_1px)] [background-size:24px_24px] opacity-50"></div>
      
      {/* Soft warm accents */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-[#d7b59c]/35 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-[#9eaf90]/25 rounded-full blur-3xl"></div>

      <div className="w-full max-w-5xl bg-[#FBF8F4]/95 border border-[#d9cab7] rounded-2xl shadow-[0_24px_60px_rgba(62,46,33,0.12)] overflow-hidden grid grid-cols-1 lg:grid-cols-12 relative z-10 backdrop-blur-xl">
        
        {/* Left Side: Visual Branding */}
        <div className="lg:col-span-7 p-8 lg:p-12 bg-gradient-to-br from-[#f1e4d6] via-[#efe3d5] to-[#e4d4c1] border-r border-[#d6c3aa]/80 flex flex-col justify-between relative overflow-hidden">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#8b634e]/10 border border-[#8b634e]/25 text-[#6c4738] text-xs font-semibold mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              <span>CPSE Material Standardization Platform</span>
            </div>
            
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#7d5a4a] via-[#a8775a] to-[#c69c6d] flex items-center justify-center text-white font-black text-2xl shadow-lg ring-2 ring-white/30">
                <Layers className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-[#2f261f] tracking-tight leading-none uppercase">NATIONAL UNIFIED</h1>
                <h2 className="text-xl font-bold text-[#6c4738] tracking-wider leading-none uppercase mt-1">MATERIAL MASTER</h2>
              </div>
            </div>

            <p className="text-sm font-semibold text-[#5f7158] tracking-wide mt-2">
              "One Nation – One Material Code"
            </p>
            <p className="text-xs text-[#685d54] mt-2 leading-relaxed max-w-md">
              Platform for CPSEs to standardize, match, rationalize, and map material master data across Oil & Gas, Power, Steel, Mining, and Heavy Engineering.
            </p>
          </div>

          <div className="my-8 py-6 px-4 bg-[#f8f3ee]/80 rounded-xl border border-[#d7cab8] relative shadow-inner">
            <div className="text-[10px] font-bold text-[#655c54] uppercase tracking-widest mb-4 flex items-center justify-between">
              <span>CPSE CODE CONVERGENCE PIPELINE</span>
              <span className="text-[#5f7158] font-mono flex items-center gap-1">● ACTIVE</span>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 bg-[#efe3d5] px-3 py-1.5 rounded-lg border border-[#d8c4ae] text-[#7a533d] font-mono font-bold">
                  <span>ONGC</span>
                  <span className="text-[#685d54] font-normal">MAT-10231</span>
                </div>
                <div className="flex-1 h-[2px] bg-gradient-to-r from-[#c58a4f]/60 via-[#b8a58d]/60 to-[#7d8f72] mx-2 relative">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-[#7d8f72] animate-ping"></div>
                </div>
                <div className="bg-[#8b634e]/15 border border-[#8b634e]/30 text-[#6c4738] px-3 py-1 rounded-lg font-mono font-bold">
                  NM-VAL-001
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-[#655c54] pt-4 border-t border-[#cab9a3]/70">
            <ShieldCheck className="w-4 h-4 text-[#5f7158] shrink-0" />
            <span>Encrypted Multi-CPSE Master Data Harmonization Grid</span>
          </div>
        </div>

        {/* Right Side: Command Center Auth Form */}
        <div className="lg:col-span-5 p-8 lg:p-12 flex flex-col justify-center bg-[#f8f3ee]">
          {/* Sign In vs Register Tabs */}
          <div className="flex border-b border-slate-800 mb-6">
            <button
              onClick={() => setIsRegister(false)}
              className={`pb-2 text-xs font-bold transition-colors uppercase tracking-wider flex-1 text-center ${
                !isRegister ? 'text-[#6c4738] border-b-2 border-[#8b634e]' : 'text-[#7a6d63] hover:text-[#443b36]'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsRegister(true)}
              className={`pb-2 text-xs font-bold transition-colors uppercase tracking-wider flex-1 text-center ${
                isRegister ? 'text-[#6c4738] border-b-2 border-[#8b634e]' : 'text-[#7a6d63] hover:text-[#443b36]'
              }`}
            >
              Register
            </button>
          </div>

          <div className="mb-4">
            <h3 className="text-xl font-bold text-[#2f261f] tracking-tight">
              {isRegister ? 'Request Officer Account' : 'Enterprise Access'}
            </h3>
            <p className="text-xs text-[#685d54] mt-1">
              {isRegister ? 'Submit your account request for system-administrator approval' : 'Sign in with your authorized CPSE credentials'}
            </p>
          </div>

          {regSuccess && (
            <div className="mb-4 bg-[#6b8d63]/10 border border-[#6b8d63]/25 text-[#4c6b4b] px-3 py-2 rounded-lg text-xs font-bold">
              {regSuccess}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="text-xs text-[#8a473c] bg-[#f0d9d4]/80 border border-[#d59c93] rounded-lg p-3">{error}</div>}
            {isRegister && (
              <>
                <div>
                  <label className="block text-xs font-medium text-[#50453f] mb-1.5">Full Name</label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-[#786d66] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="w-full bg-[#f3ece4] border border-[#d9cab7] rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#2f261f] placeholder-[#8a7f76] focus:outline-none focus:ring-2 focus:ring-[#8b634e]"
                      placeholder="e.g. Rajesh Kumar"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#50453f] mb-1.5">Assigned CPSE</label>
                  <select
                    value={cpseId}
                    onChange={(e) => setCpseId(e.target.value)}
                    required
                    className="w-full bg-[#f3ece4] border border-[#d9cab7] rounded-lg px-3 py-2.5 text-xs text-[#2f261f] focus:outline-none focus:ring-2 focus:ring-[#8b634e]"
                  >
                    <option value="">Select your CPSE</option>
                    {cpses.map(cpse => <option key={cpse.id} value={cpse.id}>{cpse.code} — {cpse.name}</option>)}
                  </select>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-medium text-[#50453f] mb-1.5">Official Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#786d66] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-[#f3ece4] border border-[#d9cab7] rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#2f261f] placeholder-[#8a7f76] focus:outline-none focus:ring-2 focus:ring-[#8b634e]"
                  placeholder="officer@numm.gov.in"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#50453f] mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#786d66] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-[#f3ece4] border border-[#d9cab7] rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#2f261f] placeholder-[#8a7f76] focus:outline-none focus:ring-2 focus:ring-[#8b634e]"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            {!isRegister && (
              <div className="flex items-center justify-between py-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-[#d1b7a1] bg-[#f3ece4] text-[#8b634e]"
                  />
                  <span className="text-xs text-[#655c54]">Remember session</span>
                </label>
                <a href="#help" className="text-xs text-[#6c4738] hover:text-[#4d352d] font-medium">Reset password?</a>
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full mt-2"
              icon={ArrowRight}
            >
              {isRegister ? 'Submit Account Request' : 'Sign In to Command Center'}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-[#d9cab7] text-center">
            <span className="inline-block text-[11px] text-[#6b625d] font-medium px-3 py-1 rounded-full bg-[#f3ece4] border border-[#d9cab7]">
              🔒 Secure Government Enterprise Access
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};
