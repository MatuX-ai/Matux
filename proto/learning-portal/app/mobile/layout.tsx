export default function MobileLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* 移动版容器：在桌面端居中限制宽度，在手机端全屏 */}
      <div className="mx-auto w-full max-w-[480px] min-h-screen bg-slate-50 relative shadow-2xl">
        {children}
      </div>
    </div>
  );
}
