package com.lanlan.lansplice;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * 配对码 <-> 密钥 <-> 网页令牌。和 Python 端必须逐字节一致。
 *
 * 单独成类的好处：它不 import 任何 android.*，可以直接用桌面 JDK
 * 编译运行，于是「手机算出来的令牌和电脑派生的是不是同一个」这件事
 * 不必上真机就能验（见 _tests/_test_android_token.py）。
 *
 * 对齐的 Python 实现：
 *   link2pc_core.code_to_key() / link2pc_core.web_token()
 */
public final class Codec {

    /** base32 字母表，去掉 0/1/I/O 这些容易抄错的字符，与 Python _ALPHABET 相同。 */
    static final String ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    static final String TOKEN_INFO = "LANSPLICE-WEB-TOKEN";

    private Codec() {
    }

    /** 'ABCD-EFGH-JKLM-NPQR' -> 10 字节。 */
    public static byte[] decodeCode(String code) throws Exception {
        if (code == null) {
            throw new Exception("配对码是空的");
        }
        String up = code.toUpperCase();
        StringBuilder clean = new StringBuilder();
        for (int i = 0; i < up.length(); i++) {
            char c = up.charAt(i);
            if (ALPHABET.indexOf(c) >= 0) {
                clean.append(c);
            }
        }
        if (clean.length() != 16) {
            throw new Exception("配对码要 16 位，现在是 " + clean.length() + " 位");
        }
        // 80 位拆进两个 long：前 9 个字符 = 45 位，后 7 个字符 = 35 位。
        // 不引 BigInteger，也就不会因为位数算错而悄悄错位。
        long hi = 0;
        long lo = 0;
        for (int i = 0; i < 9; i++) {
            hi = (hi << 5) | (ALPHABET.indexOf(clean.charAt(i)) & 0x1F);
        }
        for (int i = 9; i < 16; i++) {
            lo = (lo << 5) | (ALPHABET.indexOf(clean.charAt(i)) & 0x1F);
        }
        // n = hi * 2^35 + lo，按大端拆 10 字节：
        //   byte0..4 取 hi 的 bit44..4；byte5 = hi 低 5 位 | lo 的 bit34..32；
        //   byte6..9 取 lo 的 bit31..0
        byte[] out = new byte[10];
        for (int i = 0; i < 5; i++) {
            out[i] = (byte) ((hi >>> (37 - 8 * i)) & 0xFF);
        }
        out[5] = (byte) (((hi & 0x1F) << 3 | ((lo >>> 32) & 0x07)) & 0xFF);
        for (int i = 0; i < 4; i++) {
            out[6 + i] = (byte) ((lo >>> (24 - 8 * i)) & 0xFF);
        }
        return out;
    }

    /** 配对码 -> 网页令牌（24 位十六进制）。与 Python web_token() 同值。 */
    public static String tokenFor(String code) throws Exception {
        byte[] psk = decodeCode(code);
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(psk, "HmacSHA256"));
        byte[] d = mac.doFinal(TOKEN_INFO.getBytes("UTF-8"));
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < d.length && sb.length() < 24; i++) {
            String h = Integer.toHexString(d[i] & 0xFF);
            if (h.length() == 1) {
                sb.append('0');
            }
            sb.append(h);
        }
        return sb.substring(0, 24);
    }

    public static String hex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < b.length; i++) {
            String h = Integer.toHexString(b[i] & 0xFF);
            if (h.length() == 1) {
                sb.append('0');
            }
            sb.append(h);
        }
        return sb.toString();
    }

    /**
     * 桌面端自检用：一行一个配对码读进来，输出 key 和 token。
     * 手机上永远不会走这里，只为了让 Python 侧能对拍。
     */
    public static void main(String[] args) throws Exception {
        java.io.BufferedReader r = new java.io.BufferedReader(
                new java.io.InputStreamReader(System.in, "UTF-8"));
        String line;
        while ((line = r.readLine()) != null) {
            line = line.trim();
            if (line.length() == 0) {
                continue;
            }
            try {
                System.out.println(line + "\t" + hex(decodeCode(line)) + "\t"
                        + tokenFor(line));
            } catch (Exception e) {
                System.out.println(line + "\tERR\t" + e.getMessage());
            }
        }
    }
}
