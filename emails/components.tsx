import {
  Body,
  Button,
  Column,
  Container,
  Head,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Row,
  Section,
  Text,
} from '@react-email/components';
import * as React from 'react';

export const COLORS = {
  primary: '#8200C3',
  onPrimary: '#FFFFFF',
  accent: '#FFCC29',
  onAccent: '#000000',
  brandBlack: '#000000',
  pageBackground: '#F5F5F7',
  cardBackground: '#FFFFFF',
  panelBackground: '#F5F5F7',
  textPrimary: '#1D1D1F',
  textSecondary: '#6E6E73',
  textTertiary: '#86868B',
  border: '#E5E5EA',
};

export const FONTS = {
  display: "Outfit, 'Arial Black', Arial, sans-serif",
  body: "'Instrument Sans', Arial, Helvetica, sans-serif",
};

export const RADIUS = {
  md: '10px',
  lg: '16px',
};

export const TOKENS = {
  logoUrl: '{{logo_url}}',
  siteUrl: '{{site_url}}',
};

export const CONTACT = {
  phoneDisplay: '+234 703 543 6057',
  email: 'digital@shakaaraahllc.com',
  address: '67b Akapo Street, Omole Phase 1, Lagos',
};

export const token = (key: string): string => `{{${key}}}`;

interface BaseLayoutProps {
  preview: string;
  children: React.ReactNode;
}

const TRIBAR_PARTS = [
  { widthPercent: '29%', color: COLORS.brandBlack },
  { widthPercent: '23%', color: COLORS.accent },
  { widthPercent: '48%', color: COLORS.primary },
];

export const BaseLayout = ({ preview, children }: BaseLayoutProps) => (
  <Html lang="en">
    <Head>
      <meta name="color-scheme" content="light" />
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Outfit:wght@700&display=swap"
      />
    </Head>
    <Preview>{preview}</Preview>
    <Body style={bodyStyle}>
      <Container style={containerStyle}>
        <Section style={logoSectionStyle}>
          <Img src={TOKENS.logoUrl} width="160" alt="Shakaaraah Communications" style={logoStyle} />
        </Section>
        <Row style={tribarRowStyle}>
          {TRIBAR_PARTS.map((part) => (
            <Column
              key={part.color}
              style={{ ...tribarCellStyle, width: part.widthPercent, backgroundColor: part.color }}
            >
              &nbsp;
            </Column>
          ))}
        </Row>
        <Section style={contentStyle}>{children}</Section>
        <Section style={dividerSectionStyle}>
          <Hr style={dividerStyle} />
        </Section>
        <Section style={footerStyle}>
          <Text style={footerTextStyle}>
            Shakaaraah Communications, {CONTACT.address}
          </Text>
          <Text style={footerTextStyle}>
            <Link href="tel:+2347035436057" style={footerLinkStyle}>{CONTACT.phoneDisplay}</Link>
            {'  |  '}
            <Link href={`mailto:${CONTACT.email}`} style={footerLinkStyle}>{CONTACT.email}</Link>
          </Text>
        </Section>
      </Container>
    </Body>
  </Html>
);

const bodyStyle = {
  backgroundColor: COLORS.pageBackground,
  fontFamily: FONTS.body,
  margin: '0',
  padding: '32px 12px',
};

const containerStyle = {
  backgroundColor: COLORS.cardBackground,
  borderRadius: RADIUS.lg,
  maxWidth: '580px',
  margin: '0 auto',
  overflow: 'hidden',
};

const logoSectionStyle = { padding: '28px 40px 20px' };
const logoStyle = { display: 'block', height: 'auto' };

const tribarRowStyle = { width: '100%' };
const tribarCellStyle = { height: '8px', fontSize: '1px', lineHeight: '8px' };

const contentStyle = { padding: '36px 40px 12px' };

const dividerSectionStyle = { padding: '24px 40px 0' };

const dividerStyle = {
  borderColor: COLORS.border,
  margin: '0',
};

const footerStyle = { padding: '20px 40px 32px' };

const footerTextStyle = {
  color: COLORS.textTertiary,
  fontSize: '13px',
  lineHeight: '1.6',
  margin: '0 0 4px 0',
};

const footerLinkStyle = { color: COLORS.textSecondary, textDecoration: 'underline' };

interface EmailButtonProps {
  href: string;
  children: React.ReactNode;
}

export const EmailButton = ({ href, children }: EmailButtonProps) => (
  <Button href={href} style={buttonStyle}>
    {children}
  </Button>
);

const buttonStyle = {
  backgroundColor: COLORS.primary,
  borderRadius: RADIUS.md,
  color: COLORS.onPrimary,
  display: 'inline-block',
  fontFamily: FONTS.body,
  fontSize: '15px',
  fontWeight: '600',
  padding: '14px 24px',
  textDecoration: 'none',
};

export interface DetailItem {
  label: string;
  value: string;
}

interface DetailListProps {
  items: DetailItem[];
}

export const DetailList = ({ items }: DetailListProps) => (
  <Section style={panelStyle}>
    {items.map((item) => (
      <Row key={item.label} style={rowStyle}>
        <Column style={labelColumnStyle}>
          <Text style={labelStyle}>{item.label}</Text>
        </Column>
        <Column style={valueColumnStyle}>
          <Text style={valueStyle}>{item.value}</Text>
        </Column>
      </Row>
    ))}
  </Section>
);

const panelStyle = {
  backgroundColor: COLORS.panelBackground,
  borderRadius: RADIUS.md,
  padding: '12px 20px',
  margin: '0 0 28px 0',
};

const rowStyle = { borderBottom: `1px solid ${COLORS.border}` };
const labelColumnStyle = { width: '34%', verticalAlign: 'top' as const };
const valueColumnStyle = { verticalAlign: 'top' as const };

const labelStyle = {
  color: COLORS.textSecondary,
  fontSize: '13px',
  fontWeight: '500',
  lineHeight: '1.5',
  margin: '10px 0',
};

const valueStyle = {
  color: COLORS.textPrimary,
  fontFamily: FONTS.body,
  fontSize: '15px',
  lineHeight: '1.5',
  margin: '10px 0',
  whiteSpace: 'pre-wrap' as const,
  wordBreak: 'break-word' as const,
};
