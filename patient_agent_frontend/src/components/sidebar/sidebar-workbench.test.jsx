import React from 'react'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import HospitalScheduleCard from './HospitalScheduleCard.jsx'
import PatientProfileCard from './PatientProfileCard.jsx'

afterEach(() => {
  cleanup()
})

describe('PatientProfileCard', () => {
  it('renders workbench identity markers and visit summaries', () => {
    render(
      <PatientProfileCard
        profile={{
          name: '张三',
          gender: '男',
          age: 36,
          phone: '138****1024',
          idCardMasked: '1234',
          recentVisits: [
            {
              visitId: 'visit-1',
              visitDate: '2026-06-24',
              department: '消化内科',
              doctorName: '李医生',
            },
          ],
        }}
        loading={false}
        loadFailed={false}
      />
    )

    expect(screen.getByText('当前患者')).toBeInTheDocument()
    expect(screen.getByText('已建档')).toBeInTheDocument()
    expect(screen.getByText('消化内科')).toBeInTheDocument()
    expect(screen.getByText('李医生')).toBeInTheDocument()
  })
})

describe('HospitalScheduleCard', () => {
  it('selects the first department with doctors by default and switches on click', () => {
    const onSendChat = vi.fn()

    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={onSendChat}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '全科门诊',
            doctors: [],
          },
          {
            departmentId: 'dept-2',
            departmentName: '心血管内科',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王主任',
                title: '主任医师',
                bio: '擅长冠心病与高血压诊疗',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
          {
            departmentId: 'dept-3',
            departmentName: '神经内科',
            doctors: [
              {
                doctorId: 'doctor-2',
                doctorName: '赵医生',
                title: '副主任医师',
                bio: '擅长头痛与眩晕管理',
                timeSlots: ['14:00-17:30'],
              },
            ],
          },
        ]}
      />
    )

    expect(screen.getByText('王主任')).toBeInTheDocument()
    expect(screen.queryByText('点击具体科室查看排班信息')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /神经内科/ }))

    expect(screen.getByText('赵医生')).toBeInTheDocument()
  })

  it('closes the confirm modal when switching departments after choosing a doctor', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '呼吸与危重症医学科特需联合门诊',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王晓晨主任医师',
                title: '主任医师',
                bio: '擅长慢阻肺与哮喘长期管理，提供复杂呼吸系统疾病连续随访。',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
          {
            departmentId: 'dept-2',
            departmentName: '神经免疫专病门诊',
            doctors: [
              {
                doctorId: 'doctor-2',
                doctorName: '赵明远副主任医师',
                title: '副主任医师',
                bio: '擅长头痛、眩晕与自身免疫性神经疾病管理。',
                timeSlots: ['14:00-17:30'],
              },
            ],
          },
        ]}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: '预约挂号' }))

    expect(screen.getByText('确认挂号信息')).toBeInTheDocument()
    expect(screen.getAllByText('王晓晨主任医师')).toHaveLength(2)

    fireEvent.click(screen.getByRole('tab', { name: /神经免疫专病门诊/ }))

    expect(screen.queryByText('确认挂号信息')).not.toBeInTheDocument()
  })
})
