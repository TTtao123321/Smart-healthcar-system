import React, { useEffect, useMemo, useState } from 'react'
import { Calendar, Stethoscope } from 'lucide-react'
import DoctorScheduleList from './DoctorScheduleList.jsx'
import RegisterConfirmModal from './RegisterConfirmModal.jsx'

function buildDepartmentSummary(department) {
  if (!department) {
    return {
      intro: '暂无科室简介',
      morningCount: 0,
      afternoonCount: 0,
    }
  }

  const bios = []
  let morningCount = 0
  let afternoonCount = 0

  ;(department.doctors || []).forEach((doctor) => {
    const bio = doctor.bio?.trim()
    if (bio && !bios.includes(bio)) {
      bios.push(bio)
    }

    ;(doctor.timeSlots || []).forEach((slot) => {
      const [start = ''] = slot.split('-')
      const hour = Number(start.split(':')[0])
      if (Number.isNaN(hour)) return

      if (hour < 12) {
        morningCount += 1
      } else {
        afternoonCount += 1
      }
    })
  })

  const intro = bios.join('；')
  return {
    intro: intro ? `${intro.slice(0, 56)}${intro.length > 56 ? '...' : ''}` : '暂无科室简介',
    morningCount,
    afternoonCount,
  }
}

export default function HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading }) {
  const [expandedDeptIndex, setExpandedDeptIndex] = useState(null)
  const [confirmDoctor, setConfirmDoctor] = useState(null)
  const firstActiveDeptIndex = useMemo(
    () => departments.findIndex((department) => department.doctors?.length > 0),
    [departments]
  )

  useEffect(() => {
    if (departments.length === 0) {
      setExpandedDeptIndex(null)
      return
    }

    setExpandedDeptIndex(firstActiveDeptIndex >= 0 ? firstActiveDeptIndex : 0)
  }, [departments, firstActiveDeptIndex])

  const activeDepartment = expandedDeptIndex === null ? null : departments[expandedDeptIndex]
  const departmentSummary = useMemo(
    () => buildDepartmentSummary(activeDepartment),
    [activeDepartment]
  )

  useEffect(() => {
    setConfirmDoctor(null)
  }, [expandedDeptIndex])

  const handleDepartmentToggle = (index) => {
    setExpandedDeptIndex((currentIndex) => (currentIndex === index ? null : index))
  }

  const handleConfirm = () => {
    if (!activeDepartment || !confirmDoctor) return

    onSendChat(`我要预约挂号：${activeDepartment.departmentName} · ${confirmDoctor.doctorName}（${confirmDoctor.title}）`)
    setConfirmDoctor(null)
  }

  return (
    <section className="schedule-card schedule-workbench-card">
      <div className="sidebar-header schedule-workbench-header">
        <div className="schedule-workbench-title">
          <Calendar size={18} className="text-sky" />
          <span>医院排班</span>
        </div>
        <span className="schedule-workbench-caption">按科室切换</span>
      </div>

      <div className="schedule-date">{dateLabel}</div>

      {loading && <div className="schedule-loading">正在加载医院排班...</div>}

      <div className="schedule-body-scroll">
        <div className="schedule-dept-nav" role="tablist" aria-label="今日排班科室">
          {departments.map((department, index) => {
            const isActive = expandedDeptIndex === index
            return (
              <button
                key={department.departmentId}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`schedule-dept-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => handleDepartmentToggle(index)}
              >
                <span className="schedule-dept-nav-name">{department.departmentName}</span>
                <span className="schedule-dept-nav-meta">{department.doctors.length}位</span>
              </button>
            )
          })}
        </div>

        {activeDepartment ? (
          <div className="schedule-workbench-panel">
            <div className="schedule-current-dept">
              <div className="schedule-current-dept-label">当前科室</div>
              <div className="schedule-current-dept-name">{activeDepartment.departmentName}</div>
              <p className="schedule-current-dept-intro">{departmentSummary.intro}</p>
              <div className="schedule-current-dept-stats">
                <div className="schedule-current-dept-stat">
                  <span className="schedule-current-dept-stat-label">上午号源</span>
                  <span className="schedule-current-dept-stat-value">{departmentSummary.morningCount}</span>
                </div>
                <div className="schedule-current-dept-stat">
                  <span className="schedule-current-dept-stat-label">下午号源</span>
                  <span className="schedule-current-dept-stat-value">{departmentSummary.afternoonCount}</span>
                </div>
              </div>
            </div>
            <DoctorScheduleList doctors={activeDepartment.doctors} onRegister={setConfirmDoctor} />
          </div>
        ) : departments.length === 0 ? (
          <div className="schedule-placeholder">
            <Stethoscope size={30} className="placeholder-icon" />
            <p className="placeholder-text">当前暂无可展示排班</p>
          </div>
        ) : (
          <div className="schedule-placeholder">
            <Stethoscope size={30} className="placeholder-icon" />
            <p className="placeholder-text">请选择科室查看今日排班</p>
          </div>
        )}
      </div>

      <RegisterConfirmModal
        user={user}
        departmentName={activeDepartment?.departmentName || ''}
        doctor={confirmDoctor}
        dateLabel={dateLabel}
        onCancel={() => setConfirmDoctor(null)}
        onConfirm={handleConfirm}
      />
    </section>
  )
}
