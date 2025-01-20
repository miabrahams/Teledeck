import { useState, useCallback, useRef } from 'react';

export const useVideoPlayer = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const timer = useRef<number | undefined>(undefined);
  const [videoState, setVideoState] = useState({playing: false, userClick: false});

  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;

    if (videoState.playing) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
  }, [videoState]);

  const onHover = useCallback(() => {
    if (!videoRef.current) return;

    if (videoState.playing) return;

    timer.current = window.setTimeout(() => {
      videoRef.current?.play();
    }, 250);
    setVideoState({playing: true, userClick: false});
  }, []);


  const onLeave = useCallback(() => {
    if (!videoRef.current) return;

    window.clearTimeout(timer.current);
    if (videoState.userClick) return;
    videoRef.current.pause();
    setVideoState({playing: false, userClick: false});
  }, []);

  const handlePlay = useCallback(() => {
    setVideoState({playing: true, userClick: true});
  }, []);

  const handlePause = useCallback(() => {
    setVideoState({playing: false, userClick: true});
  }, []);

  return {
    videoRef,
    isPlaying: videoState,
    togglePlay,
    handlePlay,
    handlePause,
    onHover,
    onLeave,
  };
};
