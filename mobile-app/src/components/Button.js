import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { COLORS } from '../utils/constants';

const Button = ({
  title,
  onPress,
  variant = 'primary', // primary, secondary, outline, text
  size = 'medium', // small, medium, large
  disabled = false,
  loading = false,
  icon,
  style,
}) => {
  const getButtonStyle = () => {
    const base = [styles.button, styles[size]];
    
    switch (variant) {
      case 'primary':
        base.push(styles.primary);
        break;
      case 'secondary':
        base.push(styles.secondary);
        break;
      case 'outline':
        base.push(styles.outline);
        break;
      case 'text':
        base.push(styles.text);
        break;
    }
    
    if (disabled) {
      base.push(styles.disabled);
    }
    
    return base;
  };

  const getTextStyle = () => {
    const base = [styles.buttonText, styles[`${size}Text`]];
    
    switch (variant) {
      case 'primary':
        base.push(styles.primaryText);
        break;
      case 'secondary':
        base.push(styles.secondaryText);
        break;
      case 'outline':
        base.push(styles.outlineText);
        break;
      case 'text':
        base.push(styles.textText);
        break;
    }
    
    if (disabled) {
      base.push(styles.disabledText);
    }
    
    return base;
  };

  return (
    <TouchableOpacity
      style={[...getButtonStyle(), style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? '#fff' : COLORS.primary} />
      ) : (
        <>
          {icon}
          <Text style={getTextStyle()}>{title}</Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
  },
  small: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  medium: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  large: {
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  primary: {
    backgroundColor: COLORS.primary,
  },
  secondary: {
    backgroundColor: COLORS.secondary,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  text: {
    backgroundColor: 'transparent',
  },
  disabled: {
    opacity: 0.5,
  },
  buttonText: {
    fontWeight: '600',
    textAlign: 'center',
  },
  smallText: {
    fontSize: 14,
  },
  mediumText: {
    fontSize: 16,
  },
  largeText: {
    fontSize: 18,
  },
  primaryText: {
    color: '#FFFFFF',
  },
  secondaryText: {
    color: '#FFFFFF',
  },
  outlineText: {
    color: COLORS.primary,
  },
  textText: {
    color: COLORS.primary,
  },
  disabledText: {
    color: COLORS.textSecondary,
  },
});

export default Button;