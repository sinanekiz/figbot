package com.figbot.scanner;

import android.opengl.GLES11Ext;
import android.opengl.GLES20;

import com.google.ar.core.Coordinates2d;
import com.google.ar.core.Frame;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/** Minimal ARCore external-camera-texture renderer based on the public ARCore sample flow. */
final class BackgroundRenderer {
    private static final float[] QUAD_COORDS = {
            -1f, -1f,
             1f, -1f,
            -1f,  1f,
             1f,  1f
    };

    private static final String VERTEX_SHADER =
            "attribute vec4 a_Position;\n" +
            "attribute vec2 a_TexCoord;\n" +
            "varying vec2 v_TexCoord;\n" +
            "void main() { gl_Position = a_Position; v_TexCoord = a_TexCoord; }\n";

    private static final String FRAGMENT_SHADER =
            "#extension GL_OES_EGL_image_external : require\n" +
            "precision mediump float;\n" +
            "uniform samplerExternalOES u_Texture;\n" +
            "varying vec2 v_TexCoord;\n" +
            "void main() { gl_FragColor = texture2D(u_Texture, v_TexCoord); }\n";

    private final FloatBuffer quadVertices = floatBuffer(QUAD_COORDS);
    private final FloatBuffer cameraTexCoords = floatBuffer(new float[8]);
    private int textureId = -1;
    private int program;
    private int positionAttribute;
    private int texCoordAttribute;
    private boolean geometryDirty=true;
    void invalidateGeometry(){geometryDirty=true;}

    int getTextureId() {
        return textureId;
    }

    void createOnGlThread() {
        geometryDirty=true;
        int[] textures = new int[1];
        GLES20.glGenTextures(1, textures, 0);
        textureId = textures[0];
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, textureId);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);

        program = linkProgram(VERTEX_SHADER, FRAGMENT_SHADER);
        positionAttribute = GLES20.glGetAttribLocation(program, "a_Position");
        texCoordAttribute = GLES20.glGetAttribLocation(program, "a_TexCoord");
        int textureUniform = GLES20.glGetUniformLocation(program, "u_Texture");
        GLES20.glUseProgram(program);
        GLES20.glUniform1i(textureUniform, 0);
    }

    void draw(Frame frame) {
        if (geometryDirty||frame.hasDisplayGeometryChanged()) {
            quadVertices.position(0);
            cameraTexCoords.position(0);
            frame.transformCoordinates2d(
                    Coordinates2d.OPENGL_NORMALIZED_DEVICE_COORDINATES,
                    quadVertices,
                    Coordinates2d.TEXTURE_NORMALIZED,
                    cameraTexCoords);
            geometryDirty=false;
        }

        if (frame.getTimestamp() == 0) {
            return;
        }

        GLES20.glDisable(GLES20.GL_DEPTH_TEST);
        GLES20.glDepthMask(false);
        GLES20.glUseProgram(program);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, textureId);

        quadVertices.position(0);
        cameraTexCoords.position(0);
        GLES20.glVertexAttribPointer(positionAttribute, 2, GLES20.GL_FLOAT, false, 0, quadVertices);
        GLES20.glVertexAttribPointer(texCoordAttribute, 2, GLES20.GL_FLOAT, false, 0, cameraTexCoords);
        GLES20.glEnableVertexAttribArray(positionAttribute);
        GLES20.glEnableVertexAttribArray(texCoordAttribute);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
        GLES20.glDisableVertexAttribArray(positionAttribute);
        GLES20.glDisableVertexAttribArray(texCoordAttribute);
        GLES20.glDepthMask(true);
    }

    private static FloatBuffer floatBuffer(float[] values) {
        FloatBuffer buffer = ByteBuffer.allocateDirect(values.length * Float.BYTES)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer();
        buffer.put(values);
        buffer.position(0);
        return buffer;
    }

    private static int linkProgram(String vertexSource, String fragmentSource) {
        int vertex = compileShader(GLES20.GL_VERTEX_SHADER, vertexSource);
        int fragment = compileShader(GLES20.GL_FRAGMENT_SHADER, fragmentSource);
        int result = GLES20.glCreateProgram();
        GLES20.glAttachShader(result, vertex);
        GLES20.glAttachShader(result, fragment);
        GLES20.glLinkProgram(result);
        int[] status = new int[1];
        GLES20.glGetProgramiv(result, GLES20.GL_LINK_STATUS, status, 0);
        if (status[0] == 0) {
            String error = GLES20.glGetProgramInfoLog(result);
            GLES20.glDeleteProgram(result);
            throw new IllegalStateException("OpenGL program link failed: " + error);
        }
        GLES20.glDeleteShader(vertex);
        GLES20.glDeleteShader(fragment);
        return result;
    }

    private static int compileShader(int type, String source) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, source);
        GLES20.glCompileShader(shader);
        int[] status = new int[1];
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, status, 0);
        if (status[0] == 0) {
            String error = GLES20.glGetShaderInfoLog(shader);
            GLES20.glDeleteShader(shader);
            throw new IllegalStateException("OpenGL shader compile failed: " + error);
        }
        return shader;
    }
}
