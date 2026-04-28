'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Code, Box, Cpu, Users, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between mx-auto px-4">
        <Link href="/" className="flex items-center space-x-2 font-bold text-xl text-primary">
          <Cpu className="h-7 w-7 text-accent" />
          <span>MatuX</span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center space-x-8 text-sm font-medium">
          <Link href="/features" className="transition-colors hover:text-accent">核心功能</Link>
          <Link href="/tech" className="transition-colors hover:text-accent">技术亮点</Link>
          <Link href="/journey" className="transition-colors hover:text-accent">用户流程</Link>
          <Link href="/about" className="transition-colors hover:text-accent">关于我们</Link>
          <Link href="/student-dashboard" className="transition-colors hover:text-accent">学生端</Link>
          <Link href="/demo" className="transition-colors hover:text-accent">在线演示</Link>
        </div>

        <div className="hidden md:flex items-center space-x-3">
          <Link
            href="/demo"
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-5 shadow-md"
          >
            开始体验
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button className="md:hidden p-2" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Nav Dropdown */}
      {isMenuOpen && (
        <div className="md:hidden border-t bg-background p-4 space-y-4 animate-in slide-in-from-top-5">
          <Link href="/features" className="block py-2 font-medium" onClick={() => setIsMenuOpen(false)}>核心功能</Link>
          <Link href="/tech" className="block py-2 font-medium" onClick={() => setIsMenuOpen(false)}>技术亮点</Link>
          <Link href="/journey" className="block py-2 font-medium" onClick={() => setIsMenuOpen(false)}>用户流程</Link>
          <Link href="/about" className="block py-2 font-medium" onClick={() => setIsMenuOpen(false)}>关于我们</Link>
          <Link href="/student-dashboard" className="block py-2 font-medium text-accent" onClick={() => setIsMenuOpen(false)}>学生端</Link>
          <Link href="/demo" className="block py-2 font-medium text-accent" onClick={() => setIsMenuOpen(false)}>在线演示</Link>
          <Link
            href="/demo"
            className="block w-full text-center rounded-md bg-primary text-primary-foreground py-2.5 font-medium"
            onClick={() => setIsMenuOpen(false)}
          >
            开始体验
          </Link>
        </div>
      )}
    </nav>
  );
}
