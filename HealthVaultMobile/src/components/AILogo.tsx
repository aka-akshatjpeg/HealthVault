import React from 'react';
import { Image, ImageStyle, StyleProp } from 'react-native';

interface AILogoProps {
  width?: number;
  height?: number;
  style?: StyleProp<ImageStyle>;
}

export function HealthVaultAILogo({ width = 200, height = 200, style }: AILogoProps) {
  return (
    <Image
      source={require('../../assets/images/healthvault-ai-logo.png')}
      style={[
        {
          width,
          height,
          resizeMode: 'contain', 
        },
        style,
      ]}
    />
  );
}
