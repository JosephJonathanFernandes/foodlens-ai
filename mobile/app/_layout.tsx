import { useEffect, useState } from 'react';
import { Stack } from 'expo-router';

export default function RootLayout() {
  const [documentReady, setDocumentReady] = useState(false);

  useEffect(() => {
    setDocumentReady(true);
  }, []);

  if (!documentReady) {
    return null;
  }

  return (
    <Stack>
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="scan" options={{ headerShown: false }} />
      <Stack.Screen name="review" options={{ headerShown: false }} />
      <Stack.Screen name="report" options={{ headerShown: false }} />
      <Stack.Screen name="ocr-results" options={{ headerShown: false }} />
      <Stack.Screen name="history" options={{ headerShown: false }} />
      <Stack.Screen name="compare" options={{ headerShown: false }} />
    </Stack>
  );
}
