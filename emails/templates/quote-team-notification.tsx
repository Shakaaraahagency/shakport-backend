import { Heading, Link, Text } from '@react-email/components';
import * as React from 'react';
import { BaseLayout, DetailList, EmailButton, COLORS, FONTS, token } from '../components';

interface QuoteTeamNotificationEmailProps {
  name: string;
  reference: string;
  service: string;
  whatsapp_number: string;
  email: string;
  source_page: string;
  received_at: string;
  message: string;
  whatsapp_chat_url: string;
}

export const QuoteTeamNotificationEmail = ({
  name = token('name'),
  reference = token('reference'),
  service = token('service'),
  whatsapp_number = token('whatsapp_number'),
  email = token('email'),
  source_page = token('source_page'),
  received_at = token('received_at'),
  message = token('message'),
  whatsapp_chat_url = token('whatsapp_chat_url'),
}: Partial<QuoteTeamNotificationEmailProps>) => (
  <BaseLayout preview={`${name} asked for a quote: ${service}`}>
    <Heading as="h1" style={headingStyle}>
      New quote request from {name}
    </Heading>
    <Text style={paragraphStyle}>Received {received_at} (Lagos time).</Text>

    <DetailList
      items={[
        { label: 'Name', value: name },
        { label: 'WhatsApp', value: whatsapp_number },
        { label: 'Email', value: email },
        { label: 'Service', value: service },
        { label: 'Sent from', value: source_page },
        { label: 'Reference', value: reference },
        { label: 'Project details', value: message },
      ]}
    />

    <EmailButton href={whatsapp_chat_url}>Reply on WhatsApp</EmailButton>
    <Text style={smallPrintStyle}>
      Prefer email? Reply to this message and it goes straight to{' '}
      <Link href={`mailto:${email}`} style={inlineLinkStyle}>{email}</Link>.
    </Text>
  </BaseLayout>
);

QuoteTeamNotificationEmail.PreviewProps = {
  name: 'Amaka',
  reference: 'SQ-7K3M9P',
  service: 'Business website (US$350 offer)',
  whatsapp_number: '+14155550123',
  email: 'amaka@example.com',
  source_page: '/website-offer',
  received_at: '13 Nov 2026, 3:45 PM',
  message: 'We sell ginger drinks in bulk and need a site that takes orders.',
  whatsapp_chat_url: 'https://wa.me/14155550123',
} satisfies QuoteTeamNotificationEmailProps;

export default QuoteTeamNotificationEmail;

const headingStyle = {
  color: COLORS.textPrimary,
  fontFamily: FONTS.display,
  fontSize: '26px',
  fontWeight: '700',
  letterSpacing: '-0.02em',
  lineHeight: '1.2',
  margin: '0 0 8px 0',
};

const paragraphStyle = {
  color: COLORS.textSecondary,
  fontSize: '15px',
  lineHeight: '1.65',
  margin: '0 0 24px 0',
};

const inlineLinkStyle = { color: COLORS.primary, fontWeight: '600' };

const smallPrintStyle = {
  color: COLORS.textTertiary,
  fontSize: '13px',
  lineHeight: '1.6',
  margin: '24px 0 0 0',
};
