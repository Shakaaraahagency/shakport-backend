import { Heading, Link, Text } from '@react-email/components';
import * as React from 'react';
import { BaseLayout, DetailList, EmailButton, COLORS, CONTACT, FONTS, TOKENS, token } from '../components';

interface QuoteConfirmationEmailProps {
  name: string;
  reference: string;
  service: string;
  whatsapp_number: string;
  email: string;
  message: string;
}

export const QuoteConfirmationEmail = ({
  name = token('name'),
  reference = token('reference'),
  service = token('service'),
  whatsapp_number = token('whatsapp_number'),
  email = token('email'),
  message = token('message'),
}: Partial<QuoteConfirmationEmailProps>) => (
  <BaseLayout preview={`Thanks, ${name}. Your quote request is with our team and we will look into it.`}>
    <Heading as="h1" style={headingStyle}>
      Welcome to Shakaaraah Communications, {name}
    </Heading>
    <Text style={paragraphStyle}>
      Thank you for reaching out. Your quote request has been sent to our team. We will look into it and get back to you on WhatsApp or by email.
    </Text>

    <Text style={sectionLabelStyle}>What you sent us</Text>
    <DetailList
      items={[
        { label: 'Reference', value: reference },
        { label: 'Service', value: service },
        { label: 'WhatsApp', value: whatsapp_number },
        { label: 'Email', value: email },
        { label: 'Your project', value: message },
      ]}
    />

    <Text style={paragraphStyle}>
      Need to add something? Reply to this email, or message us on WhatsApp at{' '}
      <Link href="https://wa.me/2347035436057" style={inlineLinkStyle}>{CONTACT.phoneDisplay}</Link>.
    </Text>
    <EmailButton href={`${TOKENS.siteUrl}/#work`}>See what we have built</EmailButton>
    <Text style={smallPrintStyle}>
      You are getting this email because this address was used to request a quote on our website. If that was not you, you can ignore it.
    </Text>
  </BaseLayout>
);

QuoteConfirmationEmail.PreviewProps = {
  name: 'Amaka',
  reference: 'SQ-7K3M9P',
  service: 'Business website (US$350 offer)',
  whatsapp_number: '+14155550123',
  email: 'amaka@example.com',
  message: 'We sell ginger drinks in bulk and need a site that takes orders.',
} satisfies QuoteConfirmationEmailProps;

export default QuoteConfirmationEmail;

const headingStyle = {
  color: COLORS.textPrimary,
  fontFamily: FONTS.display,
  fontSize: '28px',
  fontWeight: '700',
  letterSpacing: '-0.02em',
  lineHeight: '1.2',
  margin: '0 0 16px 0',
};

const paragraphStyle = {
  color: COLORS.textSecondary,
  fontSize: '15px',
  lineHeight: '1.65',
  margin: '0 0 24px 0',
};

const sectionLabelStyle = {
  color: COLORS.textPrimary,
  fontFamily: FONTS.display,
  fontSize: '16px',
  fontWeight: '700',
  margin: '0 0 8px 0',
};

const inlineLinkStyle = { color: COLORS.primary, fontWeight: '600' };

const smallPrintStyle = {
  color: COLORS.textTertiary,
  fontSize: '13px',
  lineHeight: '1.6',
  margin: '28px 0 0 0',
};
