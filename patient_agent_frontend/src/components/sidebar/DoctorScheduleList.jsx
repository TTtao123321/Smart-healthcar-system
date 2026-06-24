import React from 'react'
import { Clock } from 'lucide-react'

export default function DoctorScheduleList({ doctors, onRegister }) {
  if (!doctors || doctors.length === 0) {
    return <div className="schedule-empty">今日暂无排班</div>
  }

  return (
    <div className="schedule-list">
      {doctors.map((doctor) => (
        <div key={doctor.doctorId} className="doctor-workbench-card">
          <div className="doctor-workbench-main">
            <div className="doctor-workbench-header">
              <div className="doctor-avatar">{doctor.doctorName?.[0] || '医'}</div>
              <div className="doctor-workbench-heading">
                <div className="doctor-name">{doctor.doctorName}</div>
                <div className="doctor-title">{doctor.title || '医生'}</div>
              </div>
            </div>
            <p className="doctor-bio">{doctor.bio || '暂无医生简介'}</p>
            <div className="doctor-times">
              <Clock size={13} className="text-sky" />
              {doctor.timeSlots.map((slot) => (
                <span key={slot} className="time-slot">{slot}</span>
              ))}
            </div>
          </div>
          <button type="button" className="register-btn" onClick={() => onRegister(doctor)}>
            预约挂号
          </button>
        </div>
      ))}
    </div>
  )
}
