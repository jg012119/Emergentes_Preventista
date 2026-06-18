import React, { useState, useEffect, useRef, useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { colors as C } from '../theme';

function RealAudioRow({ uri, duration, isUser, barHeights, formatAudioTime, activeBarColor, inactiveBarColor, playButtonBg, playButtonIconColor }) {
  const player = useAudioPlayer(uri);
  const status = useAudioPlayerStatus(player);

  const isPlaying = status.isPlaying;
  const elapsedTime = status.currentTime;
  const audioDuration = status.duration || duration;

  const handlePlayPause = async () => {
    try {
      if (status.isPlaying) {
        player.pause();
      } else {
        if (status.currentTime >= (status.duration || duration)) {
          player.seekTo(0);
        }
        player.play();
      }
    } catch (error) {
      console.log("Error playing sound:", error);
    }
  };

  const totalBars = barHeights.length;
  const activeBarIndex = isPlaying
    ? Math.floor((elapsedTime / audioDuration) * totalBars)
    : (elapsedTime > 0 ? Math.floor((elapsedTime / audioDuration) * totalBars) : 0);

  return (
    <View style={s.audioRow}>
      <TouchableOpacity
        style={[s.playButton, { backgroundColor: playButtonBg }]}
        onPress={handlePlayPause}
        activeOpacity={0.8}
      >
        <Ionicons
          name={isPlaying ? 'pause' : 'play'}
          size={18}
          color={playButtonIconColor}
          style={!isPlaying ? { marginLeft: 2 } : null}
        />
      </TouchableOpacity>

      <View style={s.waveform}>
        {barHeights.map((height, index) => {
          const isActive = index < activeBarIndex;
          return (
            <View
              key={index}
              style={[
                s.bar,
                {
                  height,
                  backgroundColor: isActive ? activeBarColor : inactiveBarColor
                }
              ]}
            />
          );
        })}
      </View>

      <Text style={[s.durationText, isUser ? s.userDurationText : s.agentDurationText]}>
        {formatAudioTime(isPlaying ? elapsedTime : audioDuration)}
      </Text>
    </View>
  );
}

function FakeAudioRow({ duration, isUser, barHeights, formatAudioTime, activeBarColor, inactiveBarColor, playButtonBg, playButtonIconColor }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    if (isPlaying) {
      const intervalMs = 100;
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => {
          const next = prev + intervalMs / 1000;
          if (next >= duration) {
            clearInterval(timerRef.current);
            setIsPlaying(false);
            return 0;
          }
          return next;
        });
      }, intervalMs);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isPlaying, duration]);

  const handlePlayPause = () => {
    setIsPlaying(prev => !prev);
  };

  const totalBars = barHeights.length;
  const activeBarIndex = isPlaying
    ? Math.floor((elapsedTime / duration) * totalBars)
    : (elapsedTime > 0 ? Math.floor((elapsedTime / duration) * totalBars) : 0);

  return (
    <View style={s.audioRow}>
      <TouchableOpacity
        style={[s.playButton, { backgroundColor: playButtonBg }, s.playButtonDisabled]}
        onPress={handlePlayPause}
        disabled={true}
        activeOpacity={0.8}
      >
        <Ionicons
          name={isPlaying ? 'pause' : 'play'}
          size={18}
          color={playButtonIconColor}
          style={!isPlaying ? { marginLeft: 2 } : null}
        />
      </TouchableOpacity>

      <View style={s.waveform}>
        {barHeights.map((height, index) => {
          const isActive = index < activeBarIndex;
          return (
            <View
              key={index}
              style={[
                s.bar,
                {
                  height,
                  backgroundColor: isActive ? activeBarColor : inactiveBarColor
                }
              ]}
            />
          );
        })}
      </View>

      <Text style={[s.durationText, isUser ? s.userDurationText : s.agentDurationText]}>
        {formatAudioTime(isPlaying ? elapsedTime : duration)}
      </Text>
    </View>
  );
}

export default function VoiceNoteBubble({ text, duration = 5, isUser = true, uri = null }) {
  const hasAudio = Boolean(uri);

  // Generate waveform heights procedurally based on string hash of text to keep it consistent
  const barHeights = useMemo(() => {
    const defaultHeights = [10, 16, 22, 14, 18, 26, 12, 20, 28, 24, 16, 10, 14, 20, 26, 18, 12, 16, 22, 14, 10, 18];
    if (!text) return defaultHeights;
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      hash = text.charCodeAt(i) + ((hash << 5) - hash);
    }
    return defaultHeights.map((h, i) => {
      const offset = Math.abs((hash + i * 7) % 15); // offset 0-14
      return Math.max(8, Math.min(30, h - 5 + offset));
    });
  }, [text]);

  const formatAudioTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Waveform colors depending on user bubble vs agent bubble
  const activeBarColor = isUser ? C.white : C.accent;
  const inactiveBarColor = isUser ? 'rgba(255, 255, 255, 0.35)' : 'rgba(155, 124, 255, 0.3)';
  const playButtonBg = isUser ? 'rgba(255, 255, 255, 0.2)' : C.accentSoft;
  const playButtonIconColor = hasAudio ? (isUser ? C.white : C.accent) : inactiveBarColor;

  return (
    <View style={s.container}>
      {hasAudio ? (
        <RealAudioRow
          uri={uri}
          duration={duration}
          isUser={isUser}
          barHeights={barHeights}
          formatAudioTime={formatAudioTime}
          activeBarColor={activeBarColor}
          inactiveBarColor={inactiveBarColor}
          playButtonBg={playButtonBg}
          playButtonIconColor={playButtonIconColor}
        />
      ) : (
        <FakeAudioRow
          duration={duration}
          isUser={isUser}
          barHeights={barHeights}
          formatAudioTime={formatAudioTime}
          activeBarColor={activeBarColor}
          inactiveBarColor={inactiveBarColor}
          playButtonBg={playButtonBg}
          playButtonIconColor={playButtonIconColor}
        />
      )}

      {text ? (
        <View style={[s.transcriptContainer, isUser ? s.userTranscriptBorder : s.agentTranscriptBorder]}>
          <Text style={[s.transcriptText, isUser ? s.userTranscriptText : s.agentTranscriptText]}>
            "{text}"
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  container: {
    paddingVertical: 2,
    minWidth: 230,
  },
  audioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  playButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playButtonDisabled: {
    opacity: 0.55,
  },
  waveform: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    height: 32,
    paddingHorizontal: 4,
  },
  bar: {
    width: 3,
    borderRadius: 1.5,
    marginHorizontal: 1.5,
  },
  durationText: {
    fontSize: 11,
    fontWeight: '600',
    minWidth: 30,
    textAlign: 'right',
  },
  userDurationText: {
    color: C.whiteSoft,
  },
  agentDurationText: {
    color: C.muted,
  },
  transcriptContainer: {
    marginTop: 8,
    paddingTop: 6,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  userTranscriptBorder: {
    borderTopColor: 'rgba(255,255,255,0.2)',
  },
  agentTranscriptBorder: {
    borderTopColor: C.border,
  },
  transcriptText: {
    fontSize: 13,
    fontStyle: 'italic',
    lineHeight: 17,
  },
  userTranscriptText: {
    color: C.whiteSoft,
  },
  agentTranscriptText: {
    color: C.muted,
  },
});
