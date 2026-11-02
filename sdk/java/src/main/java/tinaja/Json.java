package tinaja;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * The little JSON the protocol needs, so the SDK has no dependencies. Objects become {@code Map<String, Object>},
 * arrays {@code List<Object>}, numbers {@code Long} or {@code Double}.
 */
public final class Json {
    private final String text;
    private int at;

    private Json(String text) {
        this.text = text;
    }

    public static Object parse(String text) {
        Json json = new Json(text);
        json.skipSpace();
        Object value = json.value();
        json.skipSpace();
        if (json.at != text.length()) throw json.error("trailing characters");
        return value;
    }

    public static String write(Object value) {
        StringBuilder out = new StringBuilder();
        write(value, out);
        return out.toString();
    }

    private static void write(Object value, StringBuilder out) {
        if (value == null) {
            out.append("null");
        } else if (value instanceof String s) {
            writeString(s, out);
        } else if (value instanceof Number || value instanceof Boolean) {
            out.append(value);
        } else if (value instanceof Map<?, ?> map) {
            out.append('{');
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) out.append(',');
                first = false;
                writeString(String.valueOf(entry.getKey()), out);
                out.append(':');
                write(entry.getValue(), out);
            }
            out.append('}');
        } else if (value instanceof Iterable<?> list) {
            out.append('[');
            boolean first = true;
            for (Object item : list) {
                if (!first) out.append(',');
                first = false;
                write(item, out);
            }
            out.append(']');
        } else {
            throw new IllegalArgumentException("can't write " + value.getClass() + " as JSON");
        }
    }

    private static void writeString(String s, StringBuilder out) {
        out.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 0x20) out.append(String.format("\\u%04x", (int) c));
                    else out.append(c);
                }
            }
        }
        out.append('"');
    }

    private Object value() {
        if (at >= text.length()) throw error("unexpected end");
        char c = text.charAt(at);
        return switch (c) {
            case '{' -> object();
            case '[' -> array();
            case '"' -> string();
            case 't' -> literal("true", Boolean.TRUE);
            case 'f' -> literal("false", Boolean.FALSE);
            case 'n' -> literal("null", null);
            default -> number();
        };
    }

    private Map<String, Object> object() {
        Map<String, Object> map = new LinkedHashMap<>();
        at++;
        skipSpace();
        if (peek('}')) return map;
        do {
            skipSpace();
            String key = string();
            skipSpace();
            expect(':');
            skipSpace();
            map.put(key, value());
            skipSpace();
        } while (peek(','));
        expect('}');
        return map;
    }

    private List<Object> array() {
        List<Object> list = new ArrayList<>();
        at++;
        skipSpace();
        if (peek(']')) return list;
        do {
            skipSpace();
            list.add(value());
            skipSpace();
        } while (peek(','));
        expect(']');
        return list;
    }

    private String string() {
        expect('"');
        StringBuilder out = new StringBuilder();
        while (true) {
            if (at >= text.length()) throw error("unterminated string");
            char c = text.charAt(at++);
            if (c == '"') return out.toString();
            if (c != '\\') {
                out.append(c);
                continue;
            }
            char escaped = text.charAt(at++);
            switch (escaped) {
                case 'n' -> out.append('\n');
                case 'r' -> out.append('\r');
                case 't' -> out.append('\t');
                case 'b' -> out.append('\b');
                case 'f' -> out.append('\f');
                case 'u' -> {
                    out.append((char) Integer.parseInt(text.substring(at, at + 4), 16));
                    at += 4;
                }
                default -> out.append(escaped); // \" \\ \/
            }
        }
    }

    private Object number() {
        int start = at;
        while (at < text.length() && "+-0123456789.eE".indexOf(text.charAt(at)) >= 0) at++;
        String digits = text.substring(start, at);
        if (digits.isEmpty()) throw error("unexpected character");
        if (digits.contains(".") || digits.contains("e") || digits.contains("E")) return Double.parseDouble(digits);
        return Long.parseLong(digits);
    }

    private Object literal(String word, Object value) {
        if (!text.startsWith(word, at)) throw error("unexpected character");
        at += word.length();
        return value;
    }

    private void skipSpace() {
        while (at < text.length() && Character.isWhitespace(text.charAt(at))) at++;
    }

    private boolean peek(char c) {
        if (at < text.length() && text.charAt(at) == c) {
            at++;
            return true;
        }
        return false;
    }

    private void expect(char c) {
        if (!peek(c)) throw error("expected '" + c + "'");
    }

    private IllegalArgumentException error(String problem) {
        return new IllegalArgumentException("bad JSON at " + at + ": " + problem);
    }
}
