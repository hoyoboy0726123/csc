import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import * as monaco from 'monaco-editor';

const MonacoEditor = forwardRef(({ value, language = 'plaintext', theme = 'vs-dark', onChange, readOnly = false, height = '100%' }, ref) => {
  const containerRef = useRef(null);
  const editorRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    editorRef.current = monaco.editor.create(containerRef.current, {
      value,
      language,
      theme,
      readOnly,
      automaticLayout: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      fontSize: 14,
      lineNumbers: 'on',
      wordWrap: 'on',
      folding: true,
      renderWhitespace: 'selection',
      contextmenu: !readOnly,
    });

    const model = editorRef.current.getModel();
    if (model && onChange) {
      const disposable = model.onDidChangeContent(() => {
        onChange(editorRef.current.getValue());
      });
      return () => disposable.dispose();
    }

    return () => {
      if (editorRef.current) {
        editorRef.current.dispose();
      }
    };
  }, []);

  useEffect(() => {
    if (editorRef.current) {
      const currentValue = editorRef.current.getValue();
      if (currentValue !== value) {
        editorRef.current.setValue(value || '');
      }
    }
  }, [value]);

  useEffect(() => {
    if (editorRef.current) {
      monaco.editor.setModelLanguage(editorRef.current.getModel(), language);
    }
  }, [language]);

  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({ readOnly });
    }
  }, [readOnly]);

  useImperativeHandle(ref, () => ({
    getValue: () => editorRef.current?.getValue() || '',
    setValue: (newValue) => editorRef.current?.setValue(newValue),
    focus: () => editorRef.current?.focus(),
    getModel: () => editorRef.current?.getModel(),
  }));

  return <div ref={containerRef} style={{ height }} className="w-full" />;
});

MonacoEditor.displayName = 'MonacoEditor';

export default MonacoEditor;