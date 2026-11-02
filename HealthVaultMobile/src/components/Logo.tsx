import React from 'react';
import { Image, ImageStyle, StyleProp, View } from 'react-native';

interface LogoProps {
  variant?: 'full' | 'compact'; // full includes text, compact could just scale differently or we can just use full for now
  width?: number;
  height?: number;
  style?: StyleProp<ImageStyle>;
}

export function Logo({ variant = 'full', width = 200, height = 200, style }: LogoProps) {
  return (
    <Image
      source={require('../../assets/images/healthvault-logo-transparent.png')}
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
