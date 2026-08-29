import React, { useState } from 'react';
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
  const [role, setRole] = useState('officer');
  const [email, setEmail] = useState('officer@numm.gov.in');
  const [password, setPassword] = useState('••••••••••••');
  const [rememberMe, setRememberMe] = useState(true);
  const [regSuccess, setRegSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isRegister) {
      try {
        await authApi.register({ name, email, password, role });
        setRegSuccess('Account created successfully! Signing in...');
        setTimeout(async () => {
          await login(email, password);
          navigate('/dashboard');
        }, 1000);
      } catch (err) {
        console.error('Registration failed', err);
      }
    } else {
      await login(email, password);
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#0B1220] flex items-center justify-center p-4 md:p-8 relative overflow-hidden font-sans">
      {/* Background Decorative Grids */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40"></div>
      
      {/* Glowing Accents */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-cyan-600/20 rounded-full blur-3xl"></div>

      <div className="w-full max-w-5xl bg-[#111827]/90 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 relative z-10 backdrop-blur-xl">
        
        {/* Left Side: Visual Branding */}
        <div className="lg:col-span-7 p-8 lg:p-12 bg-gradient-to-br from-[#0B1220] via-[#0F172A] to-[#1E1B4B] border-r border-slate-800/80 flex flex-col justify-between relative overflow-hidden">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              <span>CPSE Material Standardization Platform</span>
            </div>
            
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center text-white font-black text-2xl shadow-lg ring-2 ring-white/10">
                <Layers className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-white tracking-tight leading-none uppercase">NATIONAL UNIFIED</h1>
                <h2 className="text-xl font-bold text-blue-400 tracking-wider leading-none uppercase mt-1">MATERIAL MASTER</h2>
              </div>
            </div>

            <p className="text-sm font-semibold text-cyan-400 tracking-wide mt-2">
              "One Nation – One Material Code"
            </p>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed max-w-md">
              AI-powered platform for CPSEs to standardize, match, rationalize, and map material master data across Oil & Gas, Power, Steel, Mining, and Heavy Engineering.
            </p>
          </div>

          <div className="my-8 py-6 px-4 bg-slate-950/60 rounded-xl border border-slate-800/80 relative">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center justify-between">
              <span>CPSE CODE CONVERGENCE PIPELINE</span>
              <span className="text-emerald-400 font-mono flex items-center gap-1">● AI ACTIVE</span>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-amber-400 font-mono font-bold">
                  <span>ONGC</span>
                  <span className="text-slate-400 font-normal">MAT-10231</span>
                </div>
                <div className="flex-1 h-[2px] bg-gradient-to-r from-amber-500/50 via-cyan-500/50 to-blue-500 mx-2 relative">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></div>
                </div>
                <div className="bg-blue-600/30 border border-blue-500/40 text-blue-300 px-3 py-1 rounded-lg font-mono font-bold">
                  NM-VAL-001
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400 pt-4 border-t border-slate-800/60">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Encrypted Multi-CPSE Master Data Harmonization Grid</span>
          </div>
        </div>

        {/* Right Side: Command Center Auth Form */}
        <div className="lg:col-span-5 p-8 lg:p-12 flex flex-col justify-center bg-[#111827]">
          {/* Sign In vs Register Tabs */}
          <div className="flex border-b border-slate-800 mb-6">
            <button
              onClick={() => setIsRegister(false)}
              className={`pb-2 text-xs font-bold transition-colors uppercase tracking-wider flex-1 text-center ${
                !isRegister ? 'text-blue-400 border-b-2 border-blue-500' : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsRegister(true)}
              className={`pb-2 text-xs font-bold transition-colors uppercase tracking-wider flex-1 text-center ${
                isRegister ? 'text-blue-400 border-b-2 border-blue-500' : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Register
            </button>
          </div>

          <div className="mb-4">
            <h3 className="text-xl font-bold text-white tracking-tight">
              {isRegister ? 'Create Officer Account' : 'Enterprise Access'}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              {isRegister ? 'Register your CPSE officer credentials' : 'Sign in with your authorized CPSE credentials'}
            </p>
          </div>

          {regSuccess && (
            <div className="mb-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-3 py-2 rounded-lg text-xs font-bold">
              {regSuccess}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Full Name</label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. Rajesh Kumar"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Officer Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="officer">Procurement Officer</option>
                    <option value="reviewer">Technical Reviewer</option>
                    <option value="cpse">CPSE Nodal Officer</option>
                  </select>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Official Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="officer@numm.gov.in"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-600"
                  />
                  <span className="text-xs text-slate-400">Remember session</span>
                </label>
                <a href="#help" className="text-xs text-blue-400 hover:text-blue-300 font-medium">Reset password?</a>
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
              {isRegister ? 'Complete Registration' : 'Sign In to Command Center'}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-800 text-center">
            <span className="inline-block text-[11px] text-slate-500 font-medium px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
              🔒 Secure Government Enterprise Access
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};
