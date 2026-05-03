import { useState, useEffect } from 'react';
import { 
  Sparkles, MapPin, CheckCircle2, AlertCircle, 
  Loader2, Target, Cpu, Layers, TrendingUp, Send, MessageSquare, 
  BookmarkPlus, Search, GraduationCap, BellRing, PlusCircle, 
  History, ArrowRight, BookOpen, Gift, Milestone, ExternalLink,
  Briefcase, Book, FileText, UserCheck
} from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

// Импорт методов API
import { fetchCandidates, fetchVacancies, analyzeCandidate } from './api';

// 1. ВСПОМОГАТЕЛЬНЫЕ КОМПОНЕНТЫ И ЛОГИКА
const IconMap = {
  Send, Sparkles, PlusCircle, MessageSquare, BookmarkPlus, 
  Search, GraduationCap, BellRing, Briefcase, Book, FileText, UserCheck
};

const getScoreColor = (score) => {
  if (score >= 80) return 'text-green-500';
  if (score >= 50) return 'text-yellow-500';
  return 'text-sv-red';
};

const getScoreBg = (score) => {
  if (score >= 80) return 'bg-green-500';
  if (score >= 50) return 'bg-yellow-500';
  return 'bg-sv-red';
};

const MetricBar = ({ label, score, icon: Icon }) => (
  <div className="mb-3">
    <div className="flex justify-between items-center mb-1.5">
      <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wide flex items-center gap-1.5">
        <Icon size={12} className="text-sv-blue" /> {label}
      </span>
      <span className={`text-[12px] font-black ${getScoreColor(score)}`}>{score}%</span>
    </div>
    <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
      <div className={`h-1.5 rounded-full transition-all duration-1000 ease-out ${getScoreBg(score)}`} style={{ width: `${score}%` }}></div>
    </div>
  </div>
);

export default function App() {
  const [candidates, setCandidates] = useState([]);
  const [vacancies, setVacancies] = useState([]);
  const [isLoadingDB, setIsLoadingDB] = useState(true);
  const [errorDB, setErrorDB] = useState(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [selectedVacancyId, setSelectedVacancyId] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [scanPosition, setScanPosition] = useState(0);

  useEffect(() => {
    Promise.all([fetchCandidates(), fetchVacancies()])
      .then(([cData, vData]) => {
        setCandidates(cData);
        setVacancies(vData);
        if (cData.length > 0) setSelectedCandidateId(cData[0].id.toString());
        if (vData.length > 0) setSelectedVacancyId(vData[0].id.toString());
        setIsLoadingDB(false);
      })
      .catch(err => {
        console.error("Ошибка загрузки:", err);
        setErrorDB("Ошибка подключения к серверу. Проверьте бэкенд.");
        setIsLoadingDB(false);
      });
  }, []);

  useEffect(() => {
    let interval;
    if (isAnalyzing) {
      interval = setInterval(() => setScanPosition(prev => (prev >= 100 ? 0 : prev + 2)), 30);
    }
    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const handleAnalyze = async () => {
    if (!selectedCandidateId || !selectedVacancyId) return;
    setIsAnalyzing(true);
    setAnalysisResult(null);
    try {
      const result = await analyzeCandidate(selectedCandidateId, selectedVacancyId);
      setAnalysisResult(result);
    } catch (error) {
      alert("Ошибка анализа: " + error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSearchUrl = (text) => {
    const encodedText = encodeURIComponent(text).replace(/%20/g, '+');
    return `https://people.sovcombank.ru/vacancies?text=${encodedText}`;
  };

  // ОБРАБОТЧИК КЛИКОВ ПО КНОПКАМ CTA
  const handleCtaClick = (cta) => {
    if (cta.search_query) {
      window.open(getSearchUrl(cta.search_query), '_blank');
    } else {
      alert(`Действие: ${cta.text}\n(В MVP это симулирует переход к форме или генерацию документа)`);
    }
  };

  const currentVacancy = vacancies.find(v => v.id.toString() === selectedVacancyId);
  const radarData = analysisResult ? [
    { subject: 'Хард-скиллы', score: analysisResult.metrics.hard_skills || analysisResult.metrics.hardSkills },
    { subject: 'Опыт', score: analysisResult.metrics.experience },
    { subject: 'Soft Skills', score: analysisResult.metrics.soft_skills || analysisResult.metrics.softSkills },
    { subject: 'Код', score: analysisResult.metrics.code_quality || analysisResult.metrics.codeQuality },
    { subject: 'Архитектура', score: analysisResult.metrics.architecture },
  ] : [];

  if (isLoadingDB) return <div className="min-h-screen flex items-center justify-center font-bold text-sv-blue">Загрузка данных...</div>;
  if (errorDB) return <div className="min-h-screen flex items-center justify-center font-bold text-sv-red">{errorDB}</div>;

  return (
    <div className="min-h-screen bg-white font-sans text-[#222]">
      <header className="border-b border-gray-200 py-4 px-6 md:px-12 flex justify-between items-center sticky top-0 bg-white z-20">
        <div className="flex items-center gap-6">
          <div className="font-black text-xl tracking-tight text-sv-dark flex items-center gap-2">
            <div className="w-6 h-6 bg-sv-dark rounded-full flex items-center justify-center text-white text-[10px]">С</div>
            СОВКОМБАНК
          </div>
          <span className="font-medium text-sm hidden md:block">Хочу к вам</span>
          <div className="hidden lg:flex items-center gap-2 bg-[#E6EDFF] text-sv-blue px-3 py-1 rounded-full text-xs font-medium border border-[#CCDCFF]">
            👩‍💻 Помогу тебе найти работу!
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-12 items-start">
        {/* ВАКАНСИЯ */}
        <div>
          {currentVacancy && (
            <div className="animate-in fade-in duration-500">
              <h1 className="text-4xl font-extrabold text-sv-dark mb-4 tracking-tight">{currentVacancy.title}</h1>
              <div className="flex gap-2 mb-6 text-sm">
                <span className="bg-sv-gray-bg px-3 py-1 rounded-md text-sv-dark font-medium flex items-center gap-1">
                  <MapPin size={14} className="text-sv-blue" /> База данных
                </span>
                <span className="bg-sv-gray-bg px-3 py-1 rounded-md text-sv-dark font-medium">#{currentVacancy.id}</span>
              </div>
              <div className="space-y-8 text-[15px] leading-relaxed">
                <div className="p-5 bg-sv-gray-bg/50 rounded-2xl border-l-4 border-sv-blue italic text-gray-700">
                  {currentVacancy.description}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h3 className="text-xl font-bold text-sv-dark mb-3">Требования</h3>
                    <p className="whitespace-pre-line text-gray-600">{currentVacancy.requirements}</p>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-sv-dark mb-3">Обязанности</h3>
                    <p className="whitespace-pre-line text-gray-600">{currentVacancy.responsibilities}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ПРАВАЯ ПАНЕЛЬ */}
        <div className="flex flex-col gap-6 lg:sticky lg:top-24">
          <div className="space-y-3">
            <div className="bg-sv-gray-bg p-4 rounded-2xl border border-gray-100">
              <h4 className="text-[10px] font-bold text-sv-blue uppercase mb-2 tracking-widest">Вакансия</h4>
              <select className="w-full p-2.5 text-[13px] font-medium border border-blue-200 rounded-lg bg-white outline-none" value={selectedVacancyId} onChange={(e) => { setSelectedVacancyId(e.target.value); setAnalysisResult(null); }}>
                {vacancies.map(v => <option key={v.id} value={v.id}>{v.title}</option>)}
              </select>
            </div>
            <div className="bg-blue-50/50 border border-blue-100 p-4 rounded-2xl">
              <h4 className="text-[10px] font-bold text-sv-blue uppercase mb-2 tracking-widest">Кандидат</h4>
              <select className="w-full p-2.5 text-[13px] font-medium border border-blue-200 rounded-lg bg-white outline-none" value={selectedCandidateId} onChange={(e) => { setSelectedCandidateId(e.target.value); setAnalysisResult(null); }}>
                {candidates.map(c => <option key={c.id} value={c.id}>ID {c.id} ({c.experience_years}г. опыта)</option>)}
              </select>
            </div>
          </div>

          {!analysisResult && !isAnalyzing && (
            <div className="bg-sv-gray-bg p-6 rounded-3xl flex flex-col gap-3">
              <button className="w-full bg-sv-blue text-white font-semibold py-3.5 rounded-full opacity-90 cursor-default">Откликнуться</button>
              <div className="mt-2 pt-4 border-t border-gray-200">
                <button onClick={handleAnalyze} className="relative overflow-hidden w-full bg-gradient-to-r from-[#3B5EFE] to-[#8C3BFE] text-white font-bold py-4 rounded-full shadow-lg hover:-translate-y-0.5 active:scale-95 group transition-all">
                  <div className="absolute inset-0 -translate-x-full bg-white/20 skew-x-12 group-hover:animate-[shimmer_1.5s_infinite]"></div>
                  <Sparkles size={20} className="inline mr-2 mb-0.5" /> SkillMatch AI
                </button>
              </div>
            </div>
          )}

          {isAnalyzing && (
            <div className="bg-white rounded-3xl border border-blue-100 shadow-xl overflow-hidden relative h-64 flex flex-col items-center justify-center">
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_#3B5EFE_1px,_transparent_1px)] bg-[length:16px_16px]"></div>
              <div className="absolute left-0 right-0 h-16 bg-gradient-to-b from-transparent via-sv-blue/20 to-sv-blue/40 border-b border-sv-blue z-10" style={{ top: `${scanPosition}%`, transform: 'translateY(-100%)' }}></div>
              <Cpu size={48} className="text-blue-200 mb-4 animate-pulse" />
              <p className="text-sv-blue font-bold tracking-widest text-[11px] uppercase text-center px-4">Анализируем через OpenRouter...</p>
            </div>
          )}

          {analysisResult && !isAnalyzing && (
            <div className="bg-white p-6 rounded-3xl shadow-xl border border-blue-50 animate-in relative overflow-hidden">
              <div className="flex items-end justify-between mb-4 relative z-10">
                <div>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Совместимость</p>
                  <div className={`text-6xl font-black leading-none ${getScoreColor(analysisResult.score)} tracking-tighter`}>{analysisResult.score}%</div>
                </div>
                <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center border-4 border-white shadow-sm">
                  <Target size={24} className="text-sv-blue"/>
                </div>
              </div>

              {analysisResult.history_insight && (
                <div className="mb-4 flex items-center gap-2 bg-amber-50 text-amber-700 px-3 py-2 rounded-xl border border-amber-100 text-[11px] font-bold uppercase tracking-wider relative z-10 animate-pulse">
                  <History size={14} /> {analysisResult.history_insight}
                </div>
              )}

              <div className="h-[200px] -mt-2 -mb-2 relative z-10 mix-blend-multiply">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
                    <PolarGrid stroke="#E2E8F0" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748B', fontSize: 9, fontWeight: 700 }} />
                    <Radar name="Кандидат" dataKey="score" stroke="#3B5EFE" strokeWidth={2} fill="#3B5EFE" fillOpacity={0.25} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-[#F8FAFC] p-4 rounded-2xl text-[13px] text-gray-700 italic border-l-4 border-sv-blue leading-relaxed mb-6 relative z-10">
                "{analysisResult.summary || analysisResult.feedback_text}"
              </div>

              {/* АЛЬТЕРНАТИВНЫЕ ВАКАНСИИ */}
              {analysisResult.alternative_vacancies && analysisResult.alternative_vacancies.length > 0 && (
                <div className="mb-6 relative z-10">
                  <p className="text-[10px] font-black text-gray-400 mb-3 uppercase tracking-wider italic">💡 Рекомендуем также:</p>
                  <div className="space-y-2">
                    {analysisResult.alternative_vacancies.map((alt, i) => (
                      <a key={i} href={alt.url} target="_blank" rel="noopener noreferrer" className="w-full flex items-center justify-between p-3 text-[12px] font-bold text-sv-blue bg-white border border-blue-100 rounded-xl hover:shadow-sm no-underline group transition-all">
                        {alt.title} <ArrowRight size={16} className="text-gray-400 group-hover:text-sv-blue group-hover:translate-x-1" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* КАРЬЕРНЫЙ РОУДМЭП */}
              {analysisResult.career_roadmap && (
                <div className="mb-6 relative z-10 p-4 bg-blue-50/30 rounded-2xl border border-blue-100/50">
                  <p className="text-[10px] font-black text-sv-blue mb-4 uppercase tracking-widest flex items-center gap-2">
                    <Milestone size={14} /> Карьерный маршрут
                  </p>
                  <div className="space-y-4 border-l-2 border-blue-200 ml-2 pl-4">
                    {analysisResult.career_roadmap.map((step, i) => (
                      <div key={i} className="relative">
                        <div className="absolute -left-[25px] top-0 w-4 h-4 bg-white border-2 border-sv-blue rounded-full flex items-center justify-center text-[8px] font-bold text-sv-blue">{step.step}</div>
                        <p className="text-[12px] font-bold text-sv-dark leading-tight mb-1">{step.title}</p>
                        <p className="text-[11px] text-gray-500 leading-tight">{step.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ХАБР */}
              {analysisResult.habr_article && (
                <a href={analysisResult.habr_article.url} target="_blank" rel="noopener noreferrer" className="block p-3 mb-4 border border-gray-100 rounded-xl hover:border-sv-blue hover:bg-blue-50 transition-all group no-underline relative z-10">
                  <div className="flex gap-3 items-center">
                    <div className="w-8 h-8 bg-blue-100 text-sv-blue rounded flex items-center justify-center shrink-0"><BookOpen size={16} /></div>
                    <div className="flex-1">
                      <p className="text-[12px] font-bold text-sv-dark group-hover:text-sv-blue leading-tight">{analysisResult.habr_article.title}</p>
                      <p className="text-[9px] text-gray-400 mt-0.5 uppercase">Блог Совкомбанка</p>
                    </div>
                  </div>
                </a>
              )}

              {/* ДИНАМИЧЕСКИЕ КНОПКИ (CTAs) */}
              <div className="space-y-2 relative z-10">
                {analysisResult.ctas && analysisResult.ctas.map((cta, i) => {
                  const IconCmp = IconMap[cta.icon?.toLowerCase()] || IconMap[cta.icon] || ArrowRight;
                  const baseStyle = "w-full flex items-center justify-center gap-2 py-3.5 rounded-full text-[13px] font-bold transition-all";
                  let themeStyle = "bg-gray-100 text-gray-700";
                  if (cta.style === "primary") themeStyle = "bg-sv-blue text-white hover:bg-sv-blue-hover shadow-md";
                  if (cta.style === "ai") themeStyle = "bg-gradient-to-r from-[#3B5EFE] to-[#8C3BFE] text-white shadow-md";
                  if (cta.style === "outline") themeStyle = "bg-white text-sv-blue border-2 border-sv-blue hover:bg-blue-50";

                  return (
                    <button 
                      key={i} 
                      onClick={() => handleCtaClick(cta)} 
                      className={`${baseStyle} ${themeStyle}`}
                    >
                      <IconCmp size={16} /> {cta.text}
                    </button>
                  );
                })}
              </div>

              {analysisResult.suggest_referral && analysisResult.referral_link && (
                <div className="mt-6 pt-6 border-t border-gray-100 relative z-10 text-center">
                  <a href={analysisResult.referral_link.url} target="_blank" rel="noopener noreferrer" className="block p-4 bg-gradient-to-br from-blue-50 to-white rounded-2xl border border-blue-100 no-underline group">
                    <Gift size={24} className="mx-auto mb-2 text-sv-blue" />
                    <p className="text-[13px] font-bold text-sv-dark mb-1 group-hover:text-sv-blue">{analysisResult.referral_link.text}</p>
                    <p className="text-[11px] text-gray-400 leading-tight">Получите бонус за рекомендацию!</p>
                  </a>
                </div>
              )}
              
              <button onClick={() => setAnalysisResult(null)} className="w-full mt-6 text-[11px] font-semibold text-gray-400 hover:text-sv-blue text-center underline decoration-dotted">Сбросить анализ</button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}