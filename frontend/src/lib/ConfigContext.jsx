import { createContext, useContext, useEffect, useState } from 'react'
import { getPageConfig } from './api.js'

const DEFAULT_CONFIG = {
  site_title: 'AstroVakta — Astrology Website & Business Platform',
  site_tagline: 'for astrologers',
  logo_url: '/favicon.svg',
  primary_color: '#7c3aed',
  secondary_color: '#d97706',
  homepage_hero_title: 'Astro',
  homepage_hero_subtitle: 'Vakta',
  homepage_tagline: 'The Vedic Astrology API for Modern Developers',
  homepage_description: 'Birth charts, horoscopes, doshas, compatibility, panchang, divisional charts, PDF reports, and AI interpretations — a complete sidereal astrology engine behind a single REST API.',
  contact_email: 'hello@astrovakta.com',
  contact_phone: '+91-62394-02519',
  contact_address: 'India',
  footer_text: '© 2026 AstroVakta. All rights reserved.',
  seo_title: 'AstroVakta — Create Your Astrology Website & Complete Business in a Few Clicks',
  seo_description: 'Branded astrology website with your own domain, appointment booking, WhatsApp alerts, online payments, ecommerce store, social media management and complete SEO — no coding. Plus a 216+ endpoint Vedic astrology API for developers.',
  seo_keywords: 'astrology website builder, website for astrologers, astrologer website with booking, create astrology website, kundli website, astrology business solution, astrology api, vedic astrology api',
  seo_og_image: '/og-image.png',
}

const ConfigContext = createContext({ config: DEFAULT_CONFIG })

export function ConfigProvider({ children }) {
  const [config, setConfig] = useState(DEFAULT_CONFIG)

  useEffect(() => {
    getPageConfig()
      .then((data) => {
        if (data && typeof data === 'object') setConfig({ ...DEFAULT_CONFIG, ...data })
      })
      .catch(() => {})
  }, [])

  // Apply primary/secondary colours as CSS variables + favicon
  useEffect(() => {
    const root = document.documentElement.style
    if (config.primary_color) root.setProperty('--accent-purple', config.primary_color)
    if (config.secondary_color) root.setProperty('--accent-yellow', config.secondary_color)
    if (config.logo_url) {
      let link = document.querySelector("link[rel='icon']") || document.createElement('link')
      link.rel = 'icon'
      link.href = config.logo_url
      document.head.appendChild(link)
    }
  }, [config.primary_color, config.secondary_color, config.logo_url])

  return (
    <ConfigContext.Provider value={{ config }}>
      {children}
    </ConfigContext.Provider>
  )
}

export function useConfig() {
  return useContext(ConfigContext)
}
