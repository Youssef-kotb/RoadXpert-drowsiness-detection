import streamlit as st
import cv2, dlib
from imutils import face_utils
from drowsiness import detect_drowsiness
from helpers import normalize_number, validate_egyptian_mobile
from twilio_code import send_sms
from location import get_location

st.set_page_config(page_title="RoadXpert — Driver Drowsiness", layout='centered')

# --- Session State Initialization ---
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'phone_raw' not in st.session_state:
    st.session_state.phone_raw = ''
if 'phone_normal' not in st.session_state:
    st.session_state.phone_normal = ''
if 'operator' not in st.session_state:
    st.session_state.operator = ''
if 'sms_sent' not in st.session_state:
    st.session_state.sms_sent = False
if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False
if 'frame_counter' not in st.session_state:
    st.session_state.frame_counter = 0
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False

# --- Page layout ---
st.title("👋 RoadXpert مرحبًا بك في")
st.write("شركة مسؤولة عن حماية الطرق والسائقين")

# ========== INPUT PAGE ==========
if st.session_state.step == 'input':
    st.header('أدخل رقم هاتفك (مصري فقط)')
    st.markdown("يرجى إدخال الرقم بالصيغة الدولية أو المحلية. أمثلة: `201012345678+` أو `01012345678`.")

    phone_in = st.text_input('رقم الموبايل', value=st.session_state.phone_raw, placeholder='+2010... or 010...')
    st.session_state.phone_raw = phone_in

    cols = st.columns([1, 1, 2])
    with cols[0]:
        submit = st.button('Submit')
    with cols[1]:
        clear = st.button('Clear')

    if clear:
        st.session_state.phone_raw = ''
        st.rerun()

    if submit:
        normalized = normalize_number(phone_in)
        st.session_state.phone_normal = normalized
        valid, op_or_msg = validate_egyptian_mobile(normalized)

        if not normalized:
            st.error('رقم غير مقبول. تأكد من أنه مصري ويبدأ بـ 20+ أو 01')
        elif not valid:
            st.warning(op_or_msg)
        else:
            st.success(f'الرقم صحيح ويتبع شركة: {op_or_msg}')
            st.session_state.operator = op_or_msg

            # Send confirmation SMS
            sms_text = 'لقد سجلت الرقم الخاص بك مع شركة RoadXpert لحماية الطرق.'
            ok, message_sid = send_sms(normalized, sms_text)
            if ok:
                st.session_state.sms_sent = True
                st.session_state.step = 'confirm'
                st.rerun()
            else:
                st.error('حدث خطأ أثناء إرسال الرسالة. حاول مرة أخرى.')

# ========== CONFIRM PAGE ==========
elif st.session_state.step == 'confirm':
    st.header('تحقق من رقمك')
    st.write(f'أرسلنا رسالة تأكيد إلى: **{st.session_state.phone_normal}** (شركة: {st.session_state.operator})')
    st.write('هل وصلك رسالة التأكيد؟')
    c1, c2 = st.columns(2)
    with c1:
        got = st.button('نعم، وصَلَتني')
    with c2:
        notgot = st.button('لا — راجع الرقم')

    if notgot:
        st.session_state.step = 'input'
        st.session_state.sms_sent = False
        st.rerun()

    if got:
        st.success('تم التحقق ✅ — جارِ تحويلك لصفحة المراقبة')
        st.session_state.step = 'monitor'
        st.rerun()

# ========== MONITOR PAGE ==========
elif st.session_state.step == 'monitor':
    st.header('وضع المراقبة — كاميرا السائق')
    st.write('إذا اكتُشف أن السائق نائمًا، سيتم إرسال رسالة SMS بموقعه الجغرافي.')

    start = st.button('Start Monitoring')
    stop = st.button('Stop Monitoring')

    if start:
        st.session_state.monitoring = True
    if stop:
        st.session_state.monitoring = False

    cam_placeholder = st.empty()
    status_placeholder = st.empty()

    if st.session_state.monitoring:
        st.info('المراقبة تعمل — اضغط Stop Monitoring لإيقافها')

        # Parameters
        EAR_THRESHOLD = 0.25
        CONSEC_FRAMES = 20

        # Dlib models
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ تعذر الوصول للكاميرا.")
        else:
            #bool when to stop the loop
            while st.session_state.monitoring:

                ret, frame = cap.read()
                if ret:
                    frame, ear = detect_drowsiness(frame, detector, predictor, lStart, lEnd, rStart, rEnd)

                    if ear is not None and ear < EAR_THRESHOLD:
                        st.session_state.frame_counter += 1
                        if st.session_state.frame_counter >= CONSEC_FRAMES and not st.session_state.alert_sent:
                            status_placeholder.error("😴 تنبيه: يبدو أنك نائم!")
                            cv2.putText(frame, "DROWSINESS ALERT!", (50,100),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
                            location = get_location()
                            sms_text = f'تنبيه: يبدو أن السائق نائم! موقعه التقريبي: {location}'
                            ok, message_sid = send_sms(st.session_state.phone_normal, sms_text)
                            if ok:
                                status_placeholder.success(f'تم إرسال رسالة إلى {st.session_state.phone_normal}')
                                st.session_state.alert_sent = True
                    else:
                        st.session_state.frame_counter = 0
                        st.session_state.alert_sent = False

                    # Display EAR
                    if ear is not None:
                        cv2.putText(frame, f"EAR: {ear:.2f}", (300, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

                    # Show video
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    cam_placeholder.image(frame, channels="RGB")

                if stop:
                    st.session_state.monitoring = False
                    status_placeholder.info('المراقبة متوقفة.')
                    break

            cap.release()
            cv2.destroyAllWindows()
