import { useState, useCallback } from 'react';

interface UseSwipeControlsProps {
  onSwipeLeft: () => void;
  onSwipeRight: () => void;
  onSwipeUp: () => void;
  onSwipeDown: () => void;
  onTap: () => void;
}

export const useSwipeControls = ({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  onTap,
}: UseSwipeControlsProps) => {
  const [touchStart, setTouchStart] = useState({ x: 0, y: 0 });
  const [touchEnd, setTouchEnd] = useState({ x: 0, y: 0 });

  // Minimum swipe distance to trigger an action
  const minSwipeDistance = 50;

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
  }, []);

  const onTouchEnd = useCallback(() => {
    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = touchStart.y - touchEnd.y;

    const isHorizontalSwipe = Math.abs(distanceX) > Math.abs(distanceY);

    if (isHorizontalSwipe) {
      if (distanceX > minSwipeDistance) {
        // Swipe left
        onSwipeLeft();
      } else if (distanceX < -minSwipeDistance) {
        // Swipe right
        onSwipeRight();
      } else {
        // Tap
        onTap();
      }
    } else {
      if (distanceY > minSwipeDistance) {
        // Swipe up
        onSwipeUp();
      } else if (distanceY < -minSwipeDistance) {
        // Swipe down
        onSwipeDown();
      } else {
        // Tap
        onTap();
      }
    }
  }, [touchStart, touchEnd, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, onTap, minSwipeDistance]);

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd,
    onClick: onTap, // For desktop testing
  };
};
